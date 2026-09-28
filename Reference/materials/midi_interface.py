"""
MIDI Interface Module
Handles MIDI In/Out communication
"""

import ctypes
from ctypes import wintypes
import time
import logging

logger=logging.getLogger(__name__)

# ============================================
# Windows MIDI API
# ============================================

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

class MIDIOUTCAPS(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD), ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * MAXPNAMELEN),
        ("wTechnology", wintypes.WORD),
        ("wVoices", wintypes.WORD), ("wNotes", wintypes.WORD),
        ("wChannelMask", wintypes.WORD), ("dwSupport", wintypes.DWORD)
    ]

CALLBACK = ctypes.WINFUNCTYPE(
    None, wintypes.HANDLE, wintypes.UINT, DWORD_PTR, DWORD_PTR, DWORD_PTR
)

# ===== MIDI Input =====
winmm.midiInGetNumDevs.restype = wintypes.UINT
winmm.midiInGetDevCapsW.argtypes = [wintypes.UINT, ctypes.POINTER(MIDIINCAPS), wintypes.UINT]
winmm.midiInOpen.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.UINT, DWORD_PTR, DWORD_PTR, wintypes.DWORD]
winmm.midiInStart.argtypes = [wintypes.HANDLE]
winmm.midiInStop.argtypes = [wintypes.HANDLE]
winmm.midiInReset.argtypes = [wintypes.HANDLE]
winmm.midiInClose.argtypes = [wintypes.HANDLE]
winmm.midiInPrepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]
winmm.midiInUnprepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]
winmm.midiInAddBuffer.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]

# ===== MIDI Output =====
winmm.midiOutGetNumDevs.restype = wintypes.UINT
winmm.midiOutGetDevCapsW.argtypes = [wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
winmm.midiOutOpen.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.UINT, DWORD_PTR, DWORD_PTR, wintypes.DWORD]
winmm.midiOutShortMsg.argtypes = [wintypes.HANDLE, wintypes.DWORD]
winmm.midiOutLongMsg.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]
winmm.midiOutPrepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]
winmm.midiOutUnprepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]
winmm.midiOutClose.argtypes = [wintypes.HANDLE]

class MidiIn:
    def __init__(self, device_id, callback, buffer_size=16384):
        self.device_id = device_id
        self.callback_py = callback
        self.handle = wintypes.HANDLE()
        self.cb = CALLBACK(self.callback)
        self.buffers = []
        self.running = False
        self.buffer_size = buffer_size

    def open(self):
        r = winmm.midiInOpen(
            ctypes.byref(self.handle),
            self.device_id,
            ctypes.cast(self.cb, DWORD_PTR),
            0,
            CALLBACK_FUNCTION
        )
        if r:
            raise RuntimeError(f"midiInOpen error {r}")

        for _ in range(16):
            size = self.buffer_size
            buf = ctypes.create_string_buffer(size)
            hdr = MIDIHDR()
            hdr.lpData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
            hdr.dwBufferLength = size
            self.buffers.append((buf, hdr))
            r = winmm.midiInPrepareHeader(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
            if r:
                raise RuntimeError(f"midiInPrepareHeader error {r}")
            r = winmm.midiInAddBuffer(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
            if r:
                raise RuntimeError(f"midiInAddBuffer error {r}")

        r = winmm.midiInStart(self.handle)
        if r:
            raise RuntimeError(f"midiInStart error {r}")
        self.running = True

    def callback(self, hMidiIn, wMsg, dwInstance, dwParam1, dwParam2):
        if not self.running:
            return
        try:
            if wMsg == MIM_DATA:
                packed = int(dwParam1)
                data = bytes([
                    packed & 0xFF,
                    (packed >> 8) & 0xFF,
                    (packed >> 16) & 0xFF
                ])
                self.callback_py(data, False)
            elif wMsg == MIM_LONGDATA:
                hdr_ptr = ctypes.cast(dwParam1, ctypes.POINTER(MIDIHDR))
                hdr = hdr_ptr.contents
                if hdr.dwBytesRecorded:
                    data = ctypes.string_at(hdr.lpData, hdr.dwBytesRecorded)
                    self.callback_py(data, True)
                if self.running:
                    winmm.midiInAddBuffer(self.handle, hdr_ptr, ctypes.sizeof(hdr))
        except Exception:
            logger.exception("Unhandled WinMM MIDI input callback error")

    def close(self):
        self.running = False
        if self.handle:
            try:
                winmm.midiInStop(self.handle)
            except Exception:
                logger.exception("midiInStop failed")
            time.sleep(0.01)
            try:
                winmm.midiInReset(self.handle)
            except Exception:
                logger.exception("midiInReset failed")
            time.sleep(0.01)
            for buf, hdr in self.buffers:
                try:
                    winmm.midiInUnprepareHeader(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
                except Exception:
                    logger.exception("midiInUnprepareHeader failed")
            try:
                winmm.midiInClose(self.handle)
            except Exception:
                logger.exception("midiInClose failed")
            self.handle = None

class MidiOut:
    def __init__(self, device_id):
        self.handle = wintypes.HANDLE()
        r = winmm.midiOutOpen(ctypes.byref(self.handle), device_id, 0, 0, 0)
        if r:
            raise RuntimeError(f"midiOutOpen error {r}")

    def send_note(self, note, velocity, channel=0):
        status = 0x90 + (channel & 0x0F)
        data = bytes([status, note & 0x7F, velocity & 0x7F])
        packed = int.from_bytes(data + b'\x00', 'little')
        r = winmm.midiOutShortMsg(self.handle, packed)
        if r:
            raise RuntimeError(f"midiOutShortMsg error {r}")

    def send_note_off(self, note, velocity=0, channel=0):
        """Send MIDI Note Off."""
        status = 0x80 + (channel & 0x0F)
        data = bytes([status, note & 0x7F, velocity & 0x7F])
        packed = int.from_bytes(data + b'\x00', 'little')
        r = winmm.midiOutShortMsg(self.handle, packed)
        if r:
            raise RuntimeError(f"midiOutShortMsg error {r}")

    def send_system_message(self, cmd):
        """Send system message (FA=Start, FC=Stop, FB=Continue, F8=Clock)"""
        if self.handle:
            try:
                # System messages are 1 byte, send as packed DWORD
                packed = cmd  # cmd is already a byte like 0xFA
                r = winmm.midiOutShortMsg(self.handle, packed)
                if r:
                    print(f"Send system message error: {r}")
                    return False
                return True
            except Exception as e:
                print(f"Send system message error: {e}")
                return False
        return False

    def send_sysex(self, data):
        data = bytes(data)
        buf = ctypes.create_string_buffer(data)
        hdr = MIDIHDR()
        hdr.lpData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
        hdr.dwBufferLength = len(data)
        r = winmm.midiOutPrepareHeader(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
        if r:
            raise RuntimeError(f"midiOutPrepareHeader error {r}")
        r = winmm.midiOutLongMsg(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
        for _ in range(200):
            if hdr.dwFlags & MHDR_DONE:
                break
            time.sleep(0.001)
        done = bool(hdr.dwFlags & MHDR_DONE)
        unprep = winmm.midiOutUnprepareHeader(self.handle, ctypes.byref(hdr), ctypes.sizeof(hdr))
        if r:
            raise RuntimeError(f"midiOutLongMsg error {r}")
        if not done:
            raise RuntimeError("SysEx send timeout: MHDR_DONE was not set")
        if unprep:
            raise RuntimeError(f"midiOutUnprepareHeader error {unprep}")
        return True

    def close(self):
        if self.handle:
            winmm.midiOutClose(self.handle)
            self.handle = None

def get_inputs():
    result = []
    n = winmm.midiInGetNumDevs()
    for i in range(n):
        caps = MIDIINCAPS()
        if winmm.midiInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            result.append((i, caps.szPname))
    return result

def get_outputs():
    result = []
    n = winmm.midiOutGetNumDevs()
    for i in range(n):
        caps = MIDIOUTCAPS()
        if winmm.midiOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            result.append((i, caps.szPname))
    return result