#!/usr/bin/env python3
"""UNO Synth Pro Protocol Lab v0.1.

Read-only MIDI/SysEx capture and differential analysis tool.
Unknown/experimental SysEx transmission is intentionally not implemented.
"""

from __future__ import annotations

import csv
import json
import queue
import threading
import time
import tkinter as tk
from dataclasses import dataclass, asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Iterable, Optional

from ProtocolLab.state_investigator import stable_bit_changes

try:
    import mido
    try:
        import rtmidi  # Force the bundled python-rtmidi backend in frozen builds.
        mido.set_backend("mido.backends.rtmidi")
        MIDI_BACKEND_ERROR = None
    except Exception as exc:
        MIDI_BACKEND_ERROR = str(exc)
except ImportError as exc:  # UI can still open for offline analysis/import.
    mido = None
    MIDI_BACKEND_ERROR = str(exc)

IK_HEADER = (0xF0, 0x00, 0x21, 0x1A, 0x02, 0x03)
SYSEX_END = 0xF7

# Research candidate inherited from the original UNO Synth protocol.
# This is deliberately NOT sent automatically and is NOT a Pro confirmation.
LEGACY_SEQUENCE_STATE_CANDIDATE = bytes.fromhex("F0 00 21 1A 02 03 14 F7")

# Only roles supported by project evidence. Unknown IDs stay UNKNOWN.
KNOWN_COMMANDS = {
    0x14: "LEGACY SEQUENCE STATE CANDIDATE — PRO UNVERIFIED",
    0x24: "PRESET NAME/INFO",
    0x28: "BULK PRESET WRITE / STORE — LOCKED",
    0x29: "PRESET/SEQUENCE PAGE READ",
    0x32: "CURRENT PRESET NOTIFICATION",
    0x33: "PRESET SELECT/LOAD",
    0x36: "CURRENT BUFFER LOAD CANDIDATE — UNVERIFIED",
    0x37: "CURRENT STATE READ",
    0x3C: "ARP PATTERN WRITE",
    0x3E: "ARP LIVE STATE",
}


def bytes_to_hex(data: Iterable[int]) -> str:
    return " ".join(f"{int(x) & 0xFF:02X}" for x in data)


def parse_hex(text: str) -> bytes:
    cleaned = text.replace(",", " ").replace("0x", "").replace("0X", "")
    return bytes(int(tok, 16) for tok in cleaned.split())


@dataclass(frozen=True)
class ParsedSysex:
    valid_ik: bool
    command: Optional[int]
    command_offset: Optional[int]
    direction_shape: str
    role: str
    payload: bytes

    def command_text(self) -> str:
        return "--" if self.command is None else f"0x{self.command:02X}"


def parse_ik_sysex(data: bytes) -> ParsedSysex:
    """Parse only structure that is supported by project captures.

    Request-like messages use command at byte 6:
      F0 00 21 1A 02 03 CMD ...
    Response-like messages observed in project captures use:
      F0 00 21 1A 02 03 00 CMD ...
    """
    if len(data) < 8 or tuple(data[:6]) != IK_HEADER or data[-1] != SYSEX_END:
        return ParsedSysex(False, None, None, "NON_IK_OR_MALFORMED", "UNKNOWN", b"")

    if data[6] == 0x00 and len(data) >= 9:
        cmd_offset = 7
        shape = "RESPONSE-LIKE"
    else:
        cmd_offset = 6
        shape = "REQUEST/NOTIFY-LIKE"

    cmd = data[cmd_offset]
    role = KNOWN_COMMANDS.get(cmd, "UNKNOWN")
    payload = data[cmd_offset + 1 : -1]
    return ParsedSysex(True, cmd, cmd_offset, shape, role, payload)


@dataclass
class CaptureEvent:
    t: float
    label: str
    kind: str
    hex: str
    command: str
    role: str
    shape: str
    length: int


class CaptureModel:
    def __init__(self) -> None:
        self.started = time.monotonic()
        self.events: list[CaptureEvent] = []
        self.current_label = "UNLABELED"

    def mark(self, label: str) -> None:
        self.current_label = label.strip() or "UNLABELED"

    def add_bytes(self, data: bytes, kind: str = "SYSEX") -> CaptureEvent:
        parsed = parse_ik_sysex(data)
        ev = CaptureEvent(
            t=time.monotonic() - self.started,
            label=self.current_label,
            kind=kind,
            hex=bytes_to_hex(data),
            command=parsed.command_text(),
            role=parsed.role,
            shape=parsed.direction_shape,
            length=len(data),
        )
        self.events.append(ev)
        return ev

    def events_for_label(self, label: str) -> list[CaptureEvent]:
        return [ev for ev in self.events if ev.label == label]

    def command_counts(self, label: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for ev in self.events:
            if ev.label == label:
                counts[ev.command] = counts.get(ev.command, 0) + 1
        return counts

    def payload_signatures(self, label: str) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        for ev in self.events_for_label(label):
            if ev.kind not in ("SYSEX", "IMPORTED"):
                continue
            try:
                parsed = parse_ik_sysex(parse_hex(ev.hex))
            except ValueError:
                continue
            if not parsed.valid_ik:
                continue
            out.setdefault(ev.command, set()).add(bytes_to_hex(parsed.payload))
        return out

    def unique_payloads(self, before: str, after: str) -> list[tuple[str, str]]:
        a = self.payload_signatures(before)
        b = self.payload_signatures(after)
        rows: list[tuple[str, str]] = []
        for cmd in sorted(set(a) | set(b)):
            for payload in sorted(b.get(cmd, set()) - a.get(cmd, set())):
                rows.append((cmd, payload))
        return rows

    def byte_diff_pairs(self, before: str, after: str) -> list[tuple[str, int, int, int]]:
        """Compare the last packet for each common command when lengths match."""
        a = {ev.command: ev for ev in self.events_for_label(before)}
        b = {ev.command: ev for ev in self.events_for_label(after)}
        rows: list[tuple[str, int, int, int]] = []
        for cmd in sorted(set(a) & set(b)):
            try:
                ba, bb = parse_hex(a[cmd].hex), parse_hex(b[cmd].hex)
            except ValueError:
                continue
            if len(ba) != len(bb):
                continue
            for offset, (old, new) in enumerate(zip(ba, bb)):
                if old != new:
                    rows.append((cmd, offset, old, new))
        return rows

    def diff_labels(self, before: str, after: str) -> list[tuple[str, int, int, int]]:
        a, b = self.command_counts(before), self.command_counts(after)
        keys = sorted(set(a) | set(b))
        return [(k, a.get(k, 0), b.get(k, 0), b.get(k, 0) - a.get(k, 0)) for k in keys]


class ProtocolLab(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("UNO Synth Pro Protocol Lab v0.1 — READ ONLY")
        self.geometry("1180x720")
        self.minsize(900, 560)
        self.model = CaptureModel()
        self.rx_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.inport = None
        self.outport = None
        self.show_clock_var = tk.BooleanVar(value=False)
        self.experiment_mode = tk.StringVar(value="MANUAL — DEVICE")
        self.experiment_target = tk.StringVar(value="SEQ")
        self.experiment_snapshots = {"OFF": [], "ON": []}
        self._build_ui()
        self.refresh_ports()
        self.after(50, self._drain_queue)

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="MIDI IN:").pack(side="left")
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(top, textvariable=self.port_var, width=55, state="readonly")
        self.port_combo.pack(side="left", padx=6)
        ttk.Button(top, text="Refresh", command=self.refresh_ports).pack(side="left")
        self.connect_btn = ttk.Button(top, text="Connect", command=self.toggle_connect)
        self.connect_btn.pack(side="left", padx=6)
        ttk.Label(top, text="MIDI OUT:").pack(side="left", padx=(8,0))
        self.out_var=tk.StringVar(); self.out_combo=ttk.Combobox(top,textvariable=self.out_var,width=28,state="readonly"); self.out_combo.pack(side="left",padx=4)

        ttk.Checkbutton(top, text="Show MIDI Clock (F8)", variable=self.show_clock_var).pack(side="left", padx=(10, 0))

        self.status_var = tk.StringVar(value="READ ONLY • F8 filtered • no SysEx transmit path")
        ttk.Label(top, textvariable=self.status_var).pack(side="right")

        marker = ttk.Frame(self, padding=(8, 0, 8, 8))
        marker.pack(fill="x")
        ttk.Label(marker, text="Capture label:").pack(side="left")
        self.label_var = tk.StringVar(value="BASELINE")
        ttk.Entry(marker, textvariable=self.label_var, width=28).pack(side="left", padx=6)
        ttk.Button(marker, text="MARK", command=self.set_marker).pack(side="left")
        for label in ("BASELINE", "SEQ_ON", "SEQ_OFF", "REC_ON", "REC_OFF"):
            ttk.Button(marker, text=label, command=lambda x=label: self.quick_mark(x)).pack(side="left", padx=(5, 0))

        exp = ttk.LabelFrame(self, text="SEQ / REC State Investigator", padding=8)
        exp.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(exp, text="Mode:").pack(side="left")
        ttk.Combobox(exp, textvariable=self.experiment_mode, values=("AUTO", "MANUAL — DEVICE"), width=20, state="readonly").pack(side="left", padx=5)
        ttk.Label(exp, text="Target:").pack(side="left", padx=(10,0))
        ttk.Combobox(exp, textvariable=self.experiment_target, values=("SEQ","REC"), width=7, state="readonly").pack(side="left", padx=5)
        ttk.Button(exp, text="Read 0x37", command=self.read_current_state).pack(side="left", padx=4)
        ttk.Button(exp, text="Capture OFF", command=lambda:self.capture_experiment_state("OFF")).pack(side="left", padx=4)
        ttk.Button(exp, text="Capture ON", command=lambda:self.capture_experiment_state("ON")).pack(side="left", padx=4)
        ttk.Button(exp, text="Analyze", command=self.analyze_experiment).pack(side="left", padx=4)
        ttk.Button(exp, text="Reset experiment", command=self.reset_experiment).pack(side="left", padx=4)
        self.exp_status = tk.StringVar(value="Use physical UNO button in MANUAL mode; capture repeated OFF/ON states.")
        ttk.Label(exp, textvariable=self.exp_status).pack(side="left", padx=10)\n
        columns = ("time", "label", "kind", "cmd", "role", "shape", "len", "hex")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        widths = {"time":75,"label":100,"kind":80,"cmd":65,"role":235,"shape":145,"len":55,"hex":500}
        for col in columns:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=widths[col], stretch=(col == "hex"))
        self.tree.pack(fill="both", expand=True, padx=8)

        bottom = ttk.Frame(self, padding=8)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Import HEX log", command=self.import_hex_log).pack(side="left")
        ttk.Button(bottom, text="Export JSON", command=self.export_json).pack(side="left", padx=5)
        ttk.Button(bottom, text="Export CSV", command=self.export_csv).pack(side="left")
        ttk.Button(bottom, text="Compare labels", command=self.compare_dialog).pack(side="left", padx=5)
        ttk.Button(bottom, text="Clear", command=self.clear).pack(side="right")

    def refresh_ports(self) -> None:
        if mido is None:
            self.port_combo["values"] = ()
            self.status_var.set(f"MIDI runtime unavailable: {MIDI_BACKEND_ERROR} • offline analysis available")
            return
        if MIDI_BACKEND_ERROR:
            self.port_combo["values"] = ()
            self.status_var.set(f"MIDI backend unavailable: {MIDI_BACKEND_ERROR}")
            return
        try:
            names = mido.get_input_names(); out_names=mido.get_output_names()
        except Exception as exc:
            names = []
            self.status_var.set(f"MIDI backend error: {exc}")
        self.port_combo["values"] = names
        self.out_combo["values"] = out_names if "out_names" in locals() else ()
        if not names:
            self.status_var.set("No MIDI IN ports found. Reconnect UNO, then Refresh.")
        else:
            self.status_var.set(f"Found {len(names)} MIDI IN port(s) • READ ONLY")
        if names and self.port_var.get() not in names:
            pro = next((x for x in names if "UNO" in x.upper()), names[0])
            self.port_var.set(pro)
        if "out_names" in locals() and out_names and self.out_var.get() not in out_names: self.out_var.set(next((x for x in out_names if "UNO" in x.upper()),out_names[0]))

    def toggle_connect(self) -> None:
        if self.inport is not None:
            self.inport.close()
            self.inport = None
            if self.outport is not None: self.outport.close(); self.outport=None
            self.connect_btn.configure(text="Connect")
            self.status_var.set("Disconnected • READ ONLY")
            return
        if mido is None:
            messagebox.showerror("Protocol Lab", "Install mido + a MIDI backend first.")
            return
        name = self.port_var.get()
        if not name:
            messagebox.showwarning("Protocol Lab", "Select MIDI input.")
            return
        try:
            self.inport = mido.open_input(name, callback=self._midi_callback)
            if self.out_var.get(): self.outport=mido.open_output(self.out_var.get())
        except Exception as exc:
            messagebox.showerror("Protocol Lab", str(exc))
            return
        self.connect_btn.configure(text="Disconnect")
        self.status_var.set(f"Listening: {name} • READ ONLY")

    def _midi_callback(self, msg) -> None:
        try:
            if msg.type == "sysex":
                raw = bytes([0xF0, *msg.data, 0xF7])
                self.rx_queue.put(("bytes", (raw, "SYSEX")))
            elif msg.type == "clock":
                # MIDI Clock is 24 PPQN and can flood captures. Filter F8 by default.
                if self.show_clock_var.get():
                    self.rx_queue.put(("transport", bytes([0xF8])))
            elif msg.type in ("start", "continue", "stop"):
                transport_bytes = {"start": 0xFA, "continue": 0xFB, "stop": 0xFC}
                self.rx_queue.put(("transport", bytes([transport_bytes[msg.type]])))
        except Exception as exc:
            self.rx_queue.put(("error", str(exc)))

    def _drain_queue(self) -> None:
        while True:
            try:
                kind, payload = self.rx_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "bytes":
                raw, msg_kind = payload
                self._append_event(self.model.add_bytes(raw, msg_kind))
            elif kind == "transport":
                self._append_event(self.model.add_bytes(bytes(payload), "MIDI TRANSPORT"))
            elif kind == "error":
                self.status_var.set(f"Capture error: {payload}")
        self.after(50, self._drain_queue)

    def _append_event(self, ev: CaptureEvent) -> None:
        self.tree.insert("", "end", values=(
            f"{ev.t:8.3f}", ev.label, ev.kind, ev.command, ev.role,
            ev.shape, ev.length, ev.hex,
        ))
        children = self.tree.get_children()
        if children:
            self.tree.see(children[-1])

    def read_current_state(self) -> None:
        if self.outport is None:
            self.exp_status.set("Connect MIDI OUT first."); return
        raw=bytes.fromhex("F0 00 21 1A 02 03 37 00 00 F7")
        try:
            self.outport.send(mido.Message.from_bytes(list(raw)))
            self.exp_status.set("0x37 state read sent; waiting for response.")
        except Exception as exc: self.exp_status.set(f"0x37 send error: {exc}")\n
    def _latest_state_response(self):
        for ev in reversed(self.model.events):
            if ev.command == "0x37" and ev.shape == "RESPONSE-LIKE":
                try: return parse_hex(ev.hex)
                except ValueError: return None
        return None\n
    def capture_experiment_state(self, phase: str) -> None:
        raw=self._latest_state_response()
        if raw is None:
            self.exp_status.set("No 0x37 response captured yet.")
            return
        self.experiment_snapshots[phase].append(raw)
        self.quick_mark(f"{self.experiment_target.get()}_{phase}")
        self.exp_status.set(f"{self.experiment_target.get()} {phase}: snapshot #{len(self.experiment_snapshots[phase])} captured.")\n
    def analyze_experiment(self) -> None:
        offs=self.experiment_snapshots["OFF"]; ons=self.experiment_snapshots["ON"]; n=min(len(offs),len(ons))
        if not n:
            self.exp_status.set("Need at least one OFF and one ON 0x37 snapshot.")
            return
        stable=stable_bit_changes([(offs[i],ons[i]) for i in range(n)])
        if stable:
            txt=", ".join(f"byte {o} mask 0x{m:02X} {int(a)}→{int(b)}" for o,m,a,b in stable[:12])
            self.exp_status.set(f"Stable candidates ({n} cycle(s)): {txt}")
        else: self.exp_status.set(f"No stable bit candidate across {n} cycle(s).")\n
    def reset_experiment(self) -> None:
        self.experiment_snapshots={"OFF":[],"ON":[]}
        self.exp_status.set("Experiment reset. Capture repeated OFF/ON states.")\n
    def set_marker(self) -> None:
        self.model.mark(self.label_var.get())
        self.status_var.set(f"Capture label = {self.model.current_label} • READ ONLY")

    def quick_mark(self, label: str) -> None:
        self.label_var.set(label)
        self.set_marker()

    def import_hex_log(self) -> None:
        path = filedialog.askopenfilename(title="Import HEX log", filetypes=[("Text", "*.txt *.log"), ("All", "*.*")])
        if not path:
            return
        imported = 0
        for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                data = parse_hex(line)
            except ValueError:
                continue
            if data:
                self._append_event(self.model.add_bytes(data, "IMPORTED"))
                imported += 1
        self.status_var.set(f"Imported {imported} lines • READ ONLY")

    def export_json(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            Path(path).write_text(json.dumps([asdict(x) for x in self.model.events], indent=2, ensure_ascii=False), encoding="utf-8")

    def export_csv(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(asdict(CaptureEvent(0,"","","","","","",0)).keys()))
            w.writeheader()
            for ev in self.model.events:
                w.writerow(asdict(ev))

    def compare_dialog(self) -> None:
        labels = sorted({x.label for x in self.model.events})
        if len(labels) < 2:
            messagebox.showinfo("Compare", "Capture at least two labels first.")
            return
        win = tk.Toplevel(self)
        win.title("Command count diff")
        before = tk.StringVar(value=labels[0])
        after = tk.StringVar(value=labels[-1])
        row = ttk.Frame(win, padding=8); row.pack(fill="x")
        ttk.Combobox(row, textvariable=before, values=labels, state="readonly").pack(side="left")
        ttk.Label(row, text=" → ").pack(side="left")
        ttk.Combobox(row, textvariable=after, values=labels, state="readonly").pack(side="left")
        out = tk.Text(win, width=72, height=22); out.pack(fill="both", expand=True, padx=8, pady=(0,8))
        def run():
            out.delete("1.0", "end")
            out.insert("end", "CMD     BEFORE AFTER DELTA\n")
            for cmd, a, b, d in self.model.diff_labels(before.get(), after.get()):
                out.insert("end", f"{cmd:7} {a:6} {b:5} {d:+5}\n")
        ttk.Button(row, text="Compare", command=run).pack(side="left", padx=8)
        run()

    def clear(self) -> None:
        self.model = CaptureModel()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def destroy(self) -> None:
        if self.inport is not None: self.inport.close()
        if self.outport is not None: self.outport.close()
        super().destroy()


if __name__ == "__main__":
    ProtocolLab().mainloop()
