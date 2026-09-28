import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import queue
import json
from pathlib import Path

if not hasattr(ctypes, "WinDLL"):
    raise RuntimeError("This monitor is for Windows only (WinMM MIDI API).")

winmm = ctypes.WinDLL("winmm.dll")

DWORD_PTR = ctypes.c_void_p
CALLBACK_FUNCTION = 0x00030000
MIM_DATA = 0x3C3
MIM_LONGDATA = 0x3C4
MHDR_DONE = 0x00000001
MAXPNAMELEN = 32


class MIDIINCAPS(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD),
        ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * MAXPNAMELEN),
        ("dwSupport", wintypes.DWORD),
    ]


class MIDIOUTCAPS(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD), ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * MAXPNAMELEN),
        ("wTechnology", wintypes.WORD),
        ("wVoices", wintypes.WORD), ("wNotes", wintypes.WORD),
        ("wChannelMask", wintypes.WORD), ("dwSupport", wintypes.DWORD)
    ]


class MIDIHDR(ctypes.Structure):
    _fields_ = [
        ("lpData", ctypes.POINTER(ctypes.c_char)),
        ("dwBufferLength", wintypes.DWORD),
        ("dwBytesRecorded", wintypes.DWORD),
        ("dwUser", DWORD_PTR),
        ("dwFlags", wintypes.DWORD),
        ("lpNext", ctypes.c_void_p),
        ("reserved", DWORD_PTR),
        ("dwOffset", wintypes.DWORD),
        ("dwReserved", wintypes.DWORD * 8),
    ]


CALLBACK = ctypes.WINFUNCTYPE(
    None, wintypes.HANDLE, wintypes.UINT, DWORD_PTR, DWORD_PTR, DWORD_PTR
)

# WinMM signatures
winmm.midiInGetNumDevs.restype = ctypes.c_uint
winmm.midiInGetDevCapsW.argtypes = [ctypes.c_uint, ctypes.POINTER(MIDIINCAPS), ctypes.c_uint]
winmm.midiInOpen.argtypes = [ctypes.POINTER(wintypes.HANDLE), ctypes.c_uint, DWORD_PTR, DWORD_PTR, ctypes.c_uint]
winmm.midiInStart.argtypes = [wintypes.HANDLE]
winmm.midiInStop.argtypes = [wintypes.HANDLE]
winmm.midiInReset.argtypes = [wintypes.HANDLE]
winmm.midiInClose.argtypes = [wintypes.HANDLE]
winmm.midiInPrepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), ctypes.c_uint]
winmm.midiInUnprepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), ctypes.c_uint]
winmm.midiInAddBuffer.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), ctypes.c_uint]

winmm.midiOutGetNumDevs.restype = ctypes.c_uint
winmm.midiOutGetDevCapsW.argtypes = [ctypes.c_uint, ctypes.POINTER(MIDIOUTCAPS), ctypes.c_uint]
winmm.midiOutOpen.argtypes = [ctypes.POINTER(wintypes.HANDLE), ctypes.c_uint, DWORD_PTR, DWORD_PTR, ctypes.c_uint]
winmm.midiOutShortMsg.argtypes = [wintypes.HANDLE, wintypes.DWORD]
winmm.midiOutLongMsg.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), ctypes.c_uint]
winmm.midiOutPrepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), ctypes.c_uint]
winmm.midiOutUnprepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), ctypes.c_uint]
winmm.midiOutReset.argtypes = [wintypes.HANDLE]
winmm.midiOutClose.argtypes = [wintypes.HANDLE]


def midi_short_length(status):
    if status < 0xF0:
        return 2 if (status & 0xF0) in (0xC0, 0xD0) else 3
    return {
        0xF1: 2, 0xF2: 3, 0xF3: 2,
        0xF6: 1, 0xF8: 1, 0xFA: 1, 0xFB: 1,
        0xFC: 1, 0xFE: 1, 0xFF: 1,
    }.get(status, 1)


def get_inputs():
    result = []
    for i in range(winmm.midiInGetNumDevs()):
        caps = MIDIINCAPS()
        if winmm.midiInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            result.append((i, caps.szPname))
    return result


def get_outputs():
    result = []
    for i in range(winmm.midiOutGetNumDevs()):
        caps = MIDIOUTCAPS()
        if winmm.midiOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            result.append((i, caps.szPname))
    return result


class MidiIn:
    def __init__(self, device_id, callback, source, buffer_size=32768, buffer_count=8):
        self.device_id = device_id
        self.callback_py = callback
        self.source = source
        self.buffer_size = buffer_size
        self.buffer_count = buffer_count
        self.handle = wintypes.HANDLE()
        self.cb = CALLBACK(self._callback)
        self.buffers = []
        self.running = False
        self._close_lock = threading.Lock()

    def open(self):
        r = winmm.midiInOpen(
            ctypes.byref(self.handle), self.device_id,
            ctypes.cast(self.cb, DWORD_PTR), 0, CALLBACK_FUNCTION,
        )
        if r:
            raise RuntimeError(f"midiInOpen error {r}")

        try:
            for _ in range(self.buffer_count):
                buf = ctypes.create_string_buffer(self.buffer_size)
                hdr = MIDIHDR()
                hdr.lpData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
                hdr.dwBufferLength = self.buffer_size
                r = winmm.midiInPrepareHeader(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
                if r:
                    raise RuntimeError(f"midiInPrepareHeader error {r}")
                r = winmm.midiInAddBuffer(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
                if r:
                    raise RuntimeError(f"midiInAddBuffer error {r}")
                self.buffers.append((buf, hdr))

            self.running = True
            r = winmm.midiInStart(self.handle)
            if r:
                raise RuntimeError(f"midiInStart error {r}")
        except Exception:
            self.close()
            raise

    def _callback(self, hMidiIn, wMsg, dwInstance, dwParam1, dwParam2):
        if not self.running:
            return
        try:
            if wMsg == MIM_DATA:
                packed = int(dwParam1)
                raw = bytes([
                    packed & 0xFF,
                    (packed >> 8) & 0xFF,
                    (packed >> 16) & 0xFF,
                ])
                raw = raw[:midi_short_length(raw[0])]
                self.callback_py(self.source, raw, False)

            elif wMsg == MIM_LONGDATA:
                hdr_ptr = ctypes.cast(dwParam1, ctypes.POINTER(MIDIHDR))
                hdr = hdr_ptr.contents
                if hdr.dwBytesRecorded:
                    raw = ctypes.string_at(hdr.lpData, hdr.dwBytesRecorded)
                    self.callback_py(self.source, raw, True)
                if self.running:
                    winmm.midiInAddBuffer(self.handle, hdr_ptr, ctypes.sizeof(MIDIHDR))
        except Exception:
            # Never call Tk or show dialogs from a WinMM callback thread.
            pass

    def request_stop(self):
        self.running = False
        if self.handle:
            try:
                winmm.midiInStop(self.handle)
            except Exception:
                pass
            try:
                winmm.midiInReset(self.handle)
            except Exception:
                pass

    def close(self):
        with self._close_lock:
            self.request_stop()
            if not self.handle:
                return
            # Let WinMM return any long-message buffers before unprepare.
            time.sleep(0.03)
            for _, hdr in self.buffers:
                try:
                    winmm.midiInUnprepareHeader(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
                except Exception:
                    pass
            self.buffers.clear()
            try:
                winmm.midiInClose(self.handle)
            except Exception:
                pass
            self.handle = None


class MidiOut:
    def __init__(self, device_id):
        self.device_id = device_id
        self.handle = wintypes.HANDLE()
        self._send_lock = threading.Lock()
        self._abort = threading.Event()
        r = winmm.midiOutOpen(ctypes.byref(self.handle), self.device_id, 0, 0, 0)
        if r:
            raise RuntimeError(f"midiOutOpen error {r}")

    def abort(self):
        self._abort.set()
        if self.handle:
            try:
                winmm.midiOutReset(self.handle)
            except Exception:
                pass

    def send(self, data):
        if self._abort.is_set() or not self.handle:
            return
        data = bytes(data)
        with self._send_lock:
            if self._abort.is_set() or not self.handle:
                return
            if data and data[0] == 0xF0:
                self._send_sysex(data)
            elif 1 <= len(data) <= 3:
                packed = 0
                for i, b in enumerate(data):
                    packed |= (b & 0xFF) << (8 * i)
                r = winmm.midiOutShortMsg(self.handle, packed)
                if r:
                    raise RuntimeError(f"midiOutShortMsg error {r}")

    def _send_sysex(self, data):
        buf = ctypes.create_string_buffer(data)
        hdr = MIDIHDR()
        hdr.lpData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
        hdr.dwBufferLength = len(data)
        r = winmm.midiOutPrepareHeader(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
        if r:
            raise RuntimeError(f"midiOutPrepareHeader error {r}")
        try:
            r = winmm.midiOutLongMsg(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
            if r:
                raise RuntimeError(f"midiOutLongMsg error {r}")
            deadline = time.perf_counter() + 3.0
            while not (hdr.dwFlags & MHDR_DONE):
                if self._abort.is_set():
                    break
                if time.perf_counter() >= deadline:
                    raise TimeoutError("Timeout waiting for SysEx send")
                time.sleep(0.001)
        finally:
            try:
                winmm.midiOutUnprepareHeader(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
            except Exception:
                pass

    def close(self):
        self.abort()
        with self._send_lock:
            if self.handle:
                try:
                    winmm.midiOutClose(self.handle)
                except Exception:
                    pass
                self.handle = None


TEST_CCS = (2, 3, 4, 6, 8, 10, 11, 27, 33, 34, 42, 43, 52,
            83, 84, 85, 86, 87, 88, 89, 94, 99, 106, 115, 116, 117,
            118, 119, 121, 124, 125, 126, 127)

def cc_packet(channel, number, value):
    channel, number, value = int(channel), int(number), int(value)
    if number not in TEST_CCS or not 1 <= channel <= 16 or not 0 <= value <= 127:
        raise ValueError('Channel: 1–16; value: 0–127; CC: only the 33 test numbers.')
    return bytes((0xB0 + channel - 1, number, value))

class App:
    VERSION = "1.2 Test Lab — Standalone Safe base"
    MAX_VISIBLE_ROWS = 5000

    def __init__(self, root):
        self.root = root
        root.title(f"UNO Synth Pro MIDI Monitor v{self.VERSION}")
        root.geometry("1500x880")
        root.minsize(1050, 650)

        self.uno_in = None
        self.editor_in = None
        self.uno_out = None
        self.editor_out = None
        self.inputs = []
        self.outputs = []

        self.records = []
        self.sysex_records = []
        self.record_lock = threading.Lock()
        self.capture_queue = queue.Queue(maxsize=20000)
        self.forward_queue = queue.Queue(maxsize=20000)
        self.error_queue = queue.Queue()
        self.forward_stop = threading.Event()
        self.close_started = False
        self.stopping = False
        self.running = False
        self.start_time = None
        self.clock_job = None
        self.clock_generation = 0

        # Plain Python copies are safe to read from WinMM callback threads.
        self.capture_channel = None  # None = OMNI
        self.capture_clock = False
        self.capture_active_sense = False

        self.proxy_mode = tk.BooleanVar(value=True)
        self.midi_channel_var = tk.StringVar(value="OMNI")
        self.show_clock_var = tk.BooleanVar(value=False)
        self.show_active_sense_var = tk.BooleanVar(value=False)

        self.build_ui()
        self._sync_filter_cache()
        self.refresh_devices()
        self.restore_ports()

        self.midi_channel_var.trace_add("write", lambda *_: self._sync_filter_cache())
        self.show_clock_var.trace_add("write", lambda *_: self._sync_filter_cache())
        self.show_active_sense_var.trace_add("write", lambda *_: self._sync_filter_cache())

        # Primary emergency shortcut requested for this project.
        root.bind_all("<Control-Shift-Escape>", self.emergency_stop)
        # Backup because Windows may reserve Ctrl+Shift+Esc for Task Manager.
        root.bind_all("<Control-Shift-F12>", self.emergency_stop)

        root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(25, self._drain_gui_queues)

    def restore_ports(self):
        try:
            saved = json.loads(Path(__file__).with_name('ports.json').read_text(encoding='utf-8'))
            for attr, name in saved.items():
                if attr in ('uno_in_combo','uno_out_combo','tap_in_combo','return_out_combo'):
                    combo = getattr(self, attr)
                    for value in combo['values']:
                        if str(value).split(': ',1)[-1] == name:
                            combo.set(value)
                            break
        except (OSError, ValueError):
            pass

    def send_manual(self, data):
        if not self.running or self.stopping or not self.uno_out:
            messagebox.showinfo('Test', 'Start Proxy first.')
            return
        try:
            self.forward_queue.put_nowait(('TEST→UNO', bytes(data)))
        except queue.Full:
            self.status.config(text='NOT SENT — queue full')

    def mark(self, text):
        elapsed = time.perf_counter()-self.start_time if self.start_time else 0.0
        rec = (elapsed, 'MARK', 'NOTE', 0, '', str(text), b'')
        with self.record_lock:
            self.records.append(rec)
            n = len(self.records)
        self._add_row(n, rec)

    def start_clock(self):
        if not self.running or self.stopping:
            messagebox.showinfo('Clock', 'Start Proxy first.')
            return
        try:
            bpm = int(self.bpm_var.get())
            if not 20 <= bpm <= 300: raise ValueError()
        except ValueError:
            messagebox.showerror('Clock', 'BPM must be 20–300.')
            return
        self.stop_clock()
        self.clock_interval = 60.0/(bpm*24)
        self.clock_next = time.perf_counter()
        self.mark(f'CLOCK START {bpm} BPM; timer is diagnostic, not precision hardware')
        self._clock_tick()

    def _clock_tick(self):
        if not self.running or self.stopping or self.forward_stop.is_set():
            self.clock_job = None
            return
        try:
            self.forward_queue.put_nowait((f'CLOCK:{self.clock_generation}', b'\xf8'))
        except queue.Full:
            self.stop_clock()
            return
        self.clock_next = max(self.clock_next+self.clock_interval, time.perf_counter())
        self.clock_job = self.root.after(max(1,round((self.clock_next-time.perf_counter())*1000)), self._clock_tick)

    def stop_clock(self):
        self.clock_generation += 1
        if self.clock_job is not None:
            self.root.after_cancel(self.clock_job)
            self.clock_job = None
            self.mark('CLOCK STOP')

    def _sync_filter_cache(self):
        value = self.midi_channel_var.get()
        self.capture_channel = None if value == "OMNI" else max(0, min(15, int(value) - 1))
        self.capture_clock = bool(self.show_clock_var.get())
        self.capture_active_sense = bool(self.show_active_sense_var.get())

    def build_ui(self):
        settings = ttk.LabelFrame(self.root, text="MIDI ROUTING", padding=10)
        settings.pack(fill="x", padx=8, pady=8)

        labels = [
            ("Physical UNO INPUT (UNO → Monitor)", "uno_in_combo"),
            ("Physical UNO OUTPUT (Monitor → UNO)", "uno_out_combo"),
            ("EDITOR OUT / TAP INPUT (UNO_TAP)", "tap_in_combo"),
            ("EDITOR IN / RETURN OUTPUT (UNO_RETURN)", "return_out_combo"),
        ]
        for row, (text, attr) in enumerate(labels):
            ttk.Label(settings, text=text).grid(row=row, column=0, sticky="w")
            combo = ttk.Combobox(settings, state="readonly", width=48)
            combo.grid(row=row, column=1, sticky="ew", padx=8, pady=3)
            setattr(self, attr, combo)

        ttk.Checkbutton(settings, text="PROXY MODE: Editor ↔ Monitor ↔ UNO", variable=self.proxy_mode).grid(
            row=0, column=2, columnspan=2, sticky="w", padx=(20, 8)
        )
        ttk.Label(settings, text="Capture channel").grid(row=1, column=2, sticky="e")
        self.channel_combo = ttk.Combobox(settings, state="readonly", width=8, textvariable=self.midi_channel_var)
        self.channel_combo["values"] = ["OMNI"] + [str(i) for i in range(1, 17)]
        self.channel_combo.current(0)
        self.channel_combo.grid(row=1, column=3, sticky="w", padx=8)

        filters = ttk.Frame(settings)
        filters.grid(row=2, column=2, columnspan=2, sticky="w", padx=(20, 0))
        ttk.Checkbutton(filters, text="Show MIDI Clock F8", variable=self.show_clock_var).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(filters, text="Show Active Sense FE", variable=self.show_active_sense_var).pack(side="left")

        controls = ttk.Frame(settings)
        controls.grid(row=3, column=2, columnspan=2, sticky="w", padx=(20, 0))
        ttk.Button(controls, text="Refresh", command=self.refresh_devices).pack(side="left", padx=2)
        self.start_btn = ttk.Button(controls, text="Start Proxy", command=self.toggle)
        self.start_btn.pack(side="left", padx=2)
        self.stop_btn = ttk.Button(controls, text="STOP MIDI", command=self.emergency_stop)
        self.stop_btn.pack(side="left", padx=(12, 2))
        ttk.Button(controls, text="Clear", command=self.clear).pack(side="left", padx=2)
        ttk.Button(controls, text="Save", command=self.save).pack(side="left", padx=2)
        settings.columnconfigure(1, weight=1)

        tester = ttk.LabelFrame(self.root, text="MANUAL CC TEST — 33 CC / one click = one message", padding=8)
        tester.pack(fill="x", padx=8, pady=(0, 8))
        self.test_channel = tk.StringVar(value="1")
        self.test_cc = tk.StringVar(value=str(TEST_CCS[0]))
        self.test_value = tk.StringVar(value="0")
        for label, var, values in (("Send channel", self.test_channel, tuple(range(1,17))),
                                    ("CC", self.test_cc, TEST_CCS)):
            ttk.Label(tester, text=label).pack(side="left", padx=4)
            ttk.Combobox(tester, textvariable=var, values=values, state="readonly", width=5).pack(side="left")
        ttk.Label(tester, text="Value 0–127").pack(side="left", padx=6)
        ttk.Spinbox(tester, from_=0, to=127, textvariable=self.test_value, width=5).pack(side="left")
        ttk.Button(tester, text="Send value", command=self.send_test_cc).pack(side="left", padx=6)
        for value in (0, 64, 127):
            ttk.Button(tester, text=f"Send {value}", command=lambda v=value: self.send_test_cc(v)).pack(side="left", padx=2)

        transport = ttk.LabelFrame(self.root, text="TRANSPORT / STATE — manual sends", padding=6)
        transport.pack(fill="x", padx=8, pady=(0, 6))
        for label, data in (("PLAY FA", bytes([0xFA])), ("STOP FC", bytes([0xFC])),
                            ("CONTINUE FB *", bytes([0xFB])),
                            ("MMC PLAY *", bytes.fromhex('F0 7F 7F 06 02 F7')),
                            ("MMC STOP *", bytes.fromhex('F0 7F 7F 06 01 F7')),
                            ("READ STATE 37", bytes.fromhex('F0 00 21 1A 02 03 37 00 00 F7'))):
            ttk.Button(transport, text=label, command=lambda d=data: self.send_manual(d)).pack(side="left", padx=2)
        ttk.Label(transport, text="* Not supported per UNO MIDI Chart; experimental").pack(side="left", padx=6)
        clock = ttk.Frame(self.root, padding=6)
        clock.pack(fill="x", padx=8)
        self.bpm_var = tk.StringVar(value="120")
        ttk.Label(clock, text="Clock BPM (20–300)").pack(side="left")
        ttk.Spinbox(clock, from_=20, to=300, textvariable=self.bpm_var, width=6).pack(side="left")
        ttk.Button(clock, text="Start F8", command=self.start_clock).pack(side="left", padx=4)
        ttk.Button(clock, text="Stop F8", command=self.stop_clock).pack(side="left", padx=4)
        for label in ("BEFORE", "SEQ ON", "SEQ OFF", "AFTER"):
            ttk.Button(clock, text=f"Mark {label}", command=lambda s=label: self.mark(s)).pack(side="left", padx=2)
        self.note_var = tk.StringVar()
        ttk.Entry(clock, textvariable=self.note_var, width=20).pack(side="left", padx=4)
        ttk.Button(clock, text="Add note", command=lambda: self.mark(self.note_var.get())).pack(side="left")

        info = ttk.LabelFrame(self.root, text="CAPTURE FILTER / SAFETY", padding=8)
        info.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(
            info, justify="left",
            text=(
                "F8 MIDI Clock and FE Active Sense are HIDDEN FROM THE LOG by default, but are still forwarded unchanged.\n"
                "Emergency STOP MIDI: Ctrl+Shift+Esc  |  backup: Ctrl+Shift+F12.  STOP never auto-restarts Proxy."
            )
        ).pack(anchor="w")

        status_frame = ttk.Frame(self.root, padding=(8, 0, 8, 6))
        status_frame.pack(fill="x")
        self.status = ttk.Label(status_frame, text="Ready")
        self.status.pack(side="left")

        table_frame = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        table_frame.pack(fill="both", expand=True)
        cols = ("n", "time", "dir", "type", "bytes", "hex", "decoded")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        headings = ("#", "TIME", "DIRECTION", "TYPE", "BYTES", "HEX", "DECODED")
        widths = (55, 90, 130, 80, 60, 700, 300)
        for c, title, width in zip(cols, headings, widths):
            self.tree.heading(c, text=title)
            self.tree.column(c, width=width, anchor="w")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        detail_frame = ttk.LabelFrame(self.root, text="Selected message", padding=8)
        detail_frame.pack(fill="x", padx=8, pady=(0, 8))
        self.detail = tk.Text(detail_frame, height=5)
        self.detail.pack(side="left", fill="both", expand=True)
        ttk.Button(detail_frame, text="Copy HEX", command=self.copy_hex).pack(side="right", padx=8)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh_devices(self):
        if self.running or self.stopping:
            messagebox.showwarning("MIDI", "Stop Proxy before refreshing ports.")
            return
        attrs = ('uno_in_combo','uno_out_combo','tap_in_combo','return_out_combo')
        previous = {attr:getattr(self,attr).get().split(': ',1)[-1] for attr in attrs}
        self.inputs = get_inputs()
        self.outputs = get_outputs()
        in_values = [f"{i}: {name}" for i, name in self.inputs]
        out_values = [f"{i}: {name}" for i, name in self.outputs]
        self.uno_in_combo["values"] = in_values
        self.tap_in_combo["values"] = in_values
        self.uno_out_combo["values"] = out_values
        self.return_out_combo["values"] = out_values
        self._select_by_name(self.uno_in_combo, in_values, "UNO Synth Pro")
        self._select_by_name(self.uno_out_combo, out_values, "UNO Synth Pro")
        self._select_by_name(self.tap_in_combo, in_values, "UNO_TAP")
        self._select_by_name(self.return_out_combo, out_values, "UNO_RETURN")
        for attr, name in previous.items():
            combo = getattr(self,attr)
            for value in combo['values']:
                if name and str(value).split(': ',1)[-1] == name:
                    combo.set(value)
                    break
        self.status.config(text=f"Ready — {len(in_values)} MIDI inputs / {len(out_values)} MIDI outputs")

    @staticmethod
    def _select_by_name(combo, values, needle):
        needle = needle.lower()
        for i, value in enumerate(values):
            if needle in value.lower():
                combo.current(i)
                return
        if values and combo.current() < 0:
            combo.current(0)

    def toggle(self):
        if self.running:
            self.stop_proxy()
        else:
            self.start_proxy()

    def _resolve_selection(self, combo, devices, label):
        idx = combo.current()
        if idx < 0 or idx >= len(devices):
            raise ValueError(f"Select {label}.")
        return devices[idx]

    def start_proxy(self):
        if self.stopping:
            return
        if not self.proxy_mode.get():
            messagebox.showwarning("Proxy", "Enable PROXY MODE.")
            return
        try:
            uno_in = self._resolve_selection(self.uno_in_combo, self.inputs, "Physical UNO INPUT")
            tap_in = self._resolve_selection(self.tap_in_combo, self.inputs, "TAP INPUT / UNO_TAP")
            uno_out = self._resolve_selection(self.uno_out_combo, self.outputs, "Physical UNO OUTPUT")
            return_out = self._resolve_selection(self.return_out_combo, self.outputs, "RETURN OUTPUT / UNO_RETURN")
        except ValueError as e:
            messagebox.showerror("Proxy", str(e))
            return

        if uno_in[0] == tap_in[0]:
            messagebox.showerror("Proxy", "Physical UNO INPUT and TAP INPUT must be different MIDI input ports.")
            return
        if uno_out[0] == return_out[0]:
            messagebox.showerror("Proxy", "Physical UNO OUTPUT and RETURN OUTPUT must be different MIDI output ports.")
            return
        if "uno_tap" in return_out[1].lower():
            messagebox.showerror("Proxy", "RETURN OUTPUT must NOT be UNO_TAP.\nCreate/use a separate UNO_RETURN loopMIDI port.")
            return
        if "uno_return" in tap_in[1].lower():
            messagebox.showerror("Proxy", "TAP INPUT must NOT be UNO_RETURN.\nUse UNO_TAP for Editor output.")
            return

        self.start_time = time.perf_counter()
        self.forward_stop.clear()
        self.stopping = False
        try:
            self.uno_out = MidiOut(uno_out[0])
            self.editor_out = MidiOut(return_out[0])
            self.uno_in = MidiIn(uno_in[0], self.received, "UNO→EDITOR")
            self.editor_in = MidiIn(tap_in[0], self.received, "EDITOR→UNO")
            self.uno_in.open()
            self.editor_in.open()
            self.running = True
            threading.Thread(target=self._forward_worker, daemon=True).start()
            self.start_btn.config(text="Stop Proxy")
            try:
                saved = {attr:getattr(self,attr).get().split(': ',1)[-1] for attr in
                         ('uno_in_combo','uno_out_combo','tap_in_combo','return_out_combo')}
                Path(__file__).with_name('ports.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2),encoding='utf-8')
            except OSError as exc:
                self.error_queue.put(f'Port settings not saved: {exc}')
            self.status.config(text="PROXY ACTIVE — F8 hidden from capture")
        except Exception as e:
            self.running = False
            self._async_close_all()
            messagebox.showerror("Proxy start error", str(e))

    def received(self, direction, data, is_long):
        """WinMM callback path: no Tk calls, no Tk variables, no blocking SysEx send."""
        if not self.running or self.stopping:
            return
        data = bytes(data)
        if not data:
            return

        # Forward every MIDI message, even when hidden from capture.
        try:
            self.forward_queue.put_nowait((direction, data))
        except queue.Full:
            try:
                self.error_queue.put_nowait("FORWARD QUEUE FULL — STOP MIDI")
            except queue.Full:
                pass
            return

        if not self._should_capture(data, is_long):
            return

        elapsed = 0.0 if self.start_time is None else time.perf_counter() - self.start_time
        is_sysex = bool(is_long or data[0] == 0xF0)
        typ = "SysEx" if is_sysex else "MIDI"
        hx = " ".join(f"{b:02X}" for b in data)
        decoded = self.decode(data)
        rec = (elapsed, direction, typ, len(data), hx, decoded, data)
        with self.record_lock:
            self.records.append(rec)
            if is_sysex:
                self.sysex_records.append((direction, data))
            n = len(self.records)
        try:
            self.capture_queue.put_nowait((n, rec))
        except queue.Full:
            # Captured data stays in self.records; only live UI row may be dropped.
            pass

    def send_test_cc(self, value=None):
        if not self.running or self.stopping or not self.uno_out:
            messagebox.showinfo("CC test", "Start Proxy first. CC is sent to Physical UNO OUTPUT.")
            return
        try:
            data = cc_packet(self.test_channel.get(), self.test_cc.get(),
                             self.test_value.get() if value is None else value)
        except (TypeError, ValueError) as exc:
            messagebox.showerror("CC test", str(exc))
            return
        try:
            self.forward_queue.put_nowait(("TEST→UNO", data))
            self.status.config(text=f"Queued: channel {self.test_channel.get()}, CC {data[1]}, value {data[2]}")
        except queue.Full:
            self.status.config(text="CC NOT SENT — queue full")

    def _record_test_send(self, data):
        # Record only after the MIDI output call completes; no Tk calls here.
        elapsed = time.perf_counter() - self.start_time
        rec = (elapsed, "TEST→UNO", "SysEx" if data[0]==0xF0 else "MIDI", len(data), data.hex(' ').upper(),
               self.decode(data) + ' — output call completed', data)
        with self.record_lock:
            self.records.append(rec)
            n = len(self.records)
        try:
            self.capture_queue.put_nowait((n, rec))
        except queue.Full:
            pass

    def _should_capture(self, data, is_long):
        if not data:
            return False
        status = data[0]
        if status == 0xF8 and not self.capture_clock:
            return False
        if status == 0xFE and not self.capture_active_sense:
            return False
        if not (is_long or status == 0xF0) and status < 0xF0 and self.capture_channel is not None:
            if (status & 0x0F) != self.capture_channel:
                return False
        return True

    def _forward_worker(self):
        while not self.forward_stop.is_set():
            try:
                direction, data = self.forward_queue.get(timeout=0.05)
            except queue.Empty:
                continue
            if self.forward_stop.is_set() or self.stopping:
                continue
            try:
                is_clock = direction.startswith('CLOCK:')
                if is_clock and direction != f'CLOCK:{self.clock_generation}':
                    continue
                if direction in ("EDITOR→UNO", "TEST→UNO") or is_clock:
                    out = self.uno_out
                else:
                    out = self.editor_out
                if out:
                    out.send(data)
                    if direction == "TEST→UNO" and not self.forward_stop.is_set() and not self.stopping:
                        self._record_test_send(data)
                    elif is_clock and self.capture_clock:
                        self._record_test_send(data)
            except Exception as e:
                try:
                    self.error_queue.put_nowait(f"FORWARD ERROR {direction}: {e}")
                except queue.Full:
                    pass

    def _drain_gui_queues(self):
        if self.close_started:
            return
        # Batch GUI updates so a MIDI burst cannot flood Tk with one callback per message.
        count = 0
        while count < 250:
            try:
                n, rec = self.capture_queue.get_nowait()
            except queue.Empty:
                break
            self._add_row(n, rec)
            count += 1
        try:
            err = self.error_queue.get_nowait()
        except queue.Empty:
            err = None
        if err:
            self.status.config(text=err)
        self.root.after(25, self._drain_gui_queues)

    def decode(self, data):
        if len(data)==6 and data[0:2]==bytes([0xF0,0x7F]) and data[3]==6 and data[-1]==0xF7:
            return {1:'MMC Stop',2:'MMC Play'}.get(data[4],f'MMC {data[4]:02X}')
        if data[0] == 0xF0:
            return f"SysEx ({len(data)} bytes)"
        if data[0] >= 0xF0:
            names = {
                0xF1: "MTC Quarter Frame", 0xF2: "Song Position", 0xF3: "Song Select",
                0xF6: "Tune Request", 0xF8: "Clock", 0xFA: "Start", 0xFB: "Continue",
                0xFC: "Stop", 0xFE: "Active Sense", 0xFF: "Reset",
            }
            return names.get(data[0], f"System 0x{data[0]:02X}")
        status = data[0] & 0xF0
        channel = (data[0] & 0x0F) + 1
        names = {0x80: "Note Off", 0x90: "Note On", 0xA0: "Poly AT", 0xB0: "CC", 0xC0: "Program", 0xD0: "Channel AT", 0xE0: "Pitch Bend"}
        tail = " ".join(f"{x:02X}" for x in data[1:])
        return f"{names.get(status, f'0x{status:02X}')} ch {channel} {tail}".strip()

    def _add_row(self, n, rec):
        elapsed, direction, typ, size, hx, decoded, _ = rec
        iid = self.tree.insert("", "end", values=(n, f"{elapsed:.6f}", direction, typ, size, hx, decoded))
        children = self.tree.get_children()
        excess = len(children) - self.MAX_VISIBLE_ROWS
        if excess > 0:
            for old in children[:excess]:
                self.tree.delete(old)
        self.tree.see(iid)

    def stop_proxy(self):
        if not self.running and not self.stopping:
            return
        self._begin_stop(emergency=False)

    def emergency_stop(self, _event=None):
        self._begin_stop(emergency=True)
        return "break"

    def _begin_stop(self, emergency=False):
        self.stop_clock()
        if self.stopping:
            return
        self.stopping = True
        self.running = False
        self.forward_stop.set()

        # Stop producing callbacks immediately; abort any output in progress.
        for inp in (self.uno_in, self.editor_in):
            if inp:
                inp.request_stop()
        for out in (self.uno_out, self.editor_out):
            if out:
                out.abort()

        # Drop pending forwarded traffic: STOP MIDI means no delayed messages later.
        try:
            while True:
                self.forward_queue.get_nowait()
        except queue.Empty:
            pass

        self.start_btn.config(text="Start Proxy", state="disabled")
        self.status.config(text="MIDI STOPPED" if emergency else "Stopping Proxy...")
        threading.Thread(target=self._close_worker, args=(emergency,), daemon=True).start()

    def _close_worker(self, emergency):
        self._close_all_blocking()
        if not self.close_started:
            self.root.after(0, lambda: self._finish_stop(emergency))

    def _finish_stop(self, emergency):
        self.stopping = False
        self.start_btn.config(text="Start Proxy", state="normal")
        self.status.config(text="MIDI STOPPED" if emergency else "Proxy stopped")

    def _close_all_blocking(self):
        for attr in ("uno_in", "editor_in"):
            obj = getattr(self, attr)
            if obj:
                try:
                    obj.close()
                except Exception:
                    pass
                setattr(self, attr, None)
        for attr in ("uno_out", "editor_out"):
            obj = getattr(self, attr)
            if obj:
                try:
                    obj.close()
                except Exception:
                    pass
                setattr(self, attr, None)

    def _async_close_all(self):
        self.stopping = True
        self.forward_stop.set()
        threading.Thread(target=self._close_worker, args=(False,), daemon=True).start()

    def on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])["values"]
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", f"Record: {values[0]}\nTime: {values[1]} s\nDirection: {values[2]}\nType: {values[3]}\nBytes: {values[4]}\nHEX: {values[5]}\nDecoded: {values[6]}")

    def copy_hex(self):
        sel = self.tree.selection()
        if not sel:
            return
        hx = str(self.tree.item(sel[0])["values"][5])
        self.root.clipboard_clear()
        self.root.clipboard_append(hx)
        self.status.config(text="HEX copied")

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        with self.record_lock:
            self.records.clear()
            self.sysex_records.clear()
        while not self.capture_queue.empty():
            try:
                self.capture_queue.get_nowait()
            except queue.Empty:
                break
        self.detail.delete("1.0", "end")
        self.start_time = time.perf_counter()
        self.status.config(text="Cleared — PROXY ACTIVE" if self.running else "Cleared")

    def save(self):
        with self.record_lock:
            records = list(self.records)
            sysex_records = list(self.sysex_records)
        if not records:
            messagebox.showinfo("Save", "No captured data.")
            return
        stamp = time.strftime("%Y%m%d_%H%M%S")
        filename = filedialog.asksaveasfilename(initialfile=f"uno_monitor_capture_{stamp}.txt", defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not filename:
            return
        path = Path(filename)
        with path.open("w", encoding="utf-8") as f:
            f.write(f"UNO Synth Pro MIDI Monitor v{self.VERSION}\n")
            f.write(f"UNO IN: {self.uno_in_combo.get()}\n")
            f.write(f"UNO OUT: {self.uno_out_combo.get()}\n")
            f.write(f"EDITOR OUT/TAP IN: {self.tap_in_combo.get()}\n")
            f.write(f"EDITOR IN/RETURN OUT: {self.return_out_combo.get()}\n")
            f.write(f"Clock captured: {self.capture_clock}\nActive Sense captured: {self.capture_active_sense}\n")
            f.write("REC\tTIME\tDIRECTION\tTYPE\tBYTES\tHEX\tDECODED\n")
            for i, rec in enumerate(records, 1):
                elapsed, direction, typ, size, hx, decoded, _ = rec
                f.write(f"{i}\t{elapsed:.6f}\t{direction}\t{typ}\t{size}\t{hx}\t{decoded}\n")

        combined = path.with_suffix(".syx")
        with combined.open("wb") as f:
            for _, data in sysex_records:
                f.write(data)
        for i, (direction, data) in enumerate(sysex_records, 1):
            label = "editor_to_uno" if direction == "EDITOR→UNO" else "uno_to_editor"
            path.with_name(f"{path.stem}_{label}_sysex_{i:03d}.syx").write_bytes(data)
        messagebox.showinfo("Saved", f"TXT:\n{path}\n\nCombined SYX:\n{combined}\n\nSeparate SysEx files: {len(sysex_records)}")

    def close(self):
        if self.close_started:
            return
        self.close_started = True
        self.running = False
        self.stopping = True
        self.forward_stop.set()
        for inp in (self.uno_in, self.editor_in):
            if inp:
                inp.request_stop()
        for out in (self.uno_out, self.editor_out):
            if out:
                out.abort()
        # Never make Tk wait for WinMM driver shutdown.
        threading.Thread(target=self._close_all_blocking, daemon=True).start()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
