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

try:
    import mido
except ImportError:  # UI can still open for offline analysis/import.
    mido = None

IK_HEADER = (0xF0, 0x00, 0x21, 0x1A, 0x02, 0x03)
SYSEX_END = 0xF7

# Only roles supported by project evidence. Unknown IDs stay UNKNOWN.
KNOWN_COMMANDS = {
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

    def command_counts(self, label: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for ev in self.events:
            if ev.label == label:
                counts[ev.command] = counts.get(ev.command, 0) + 1
        return counts

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

        self.status_var = tk.StringVar(value="READ ONLY • no SysEx transmit path")
        ttk.Label(top, textvariable=self.status_var).pack(side="right")

        marker = ttk.Frame(self, padding=(8, 0, 8, 8))
        marker.pack(fill="x")
        ttk.Label(marker, text="Capture label:").pack(side="left")
        self.label_var = tk.StringVar(value="BASELINE")
        ttk.Entry(marker, textvariable=self.label_var, width=28).pack(side="left", padx=6)
        ttk.Button(marker, text="MARK", command=self.set_marker).pack(side="left")
        for label in ("BASELINE", "SEQ_ON", "SEQ_OFF", "REC_ON", "REC_OFF"):
            ttk.Button(marker, text=label, command=lambda x=label: self.quick_mark(x)).pack(side="left", padx=(5, 0))

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
            self.status_var.set("mido not installed • offline analysis available")
            return
        try:
            names = mido.get_input_names()
        except Exception as exc:
            names = []
            self.status_var.set(f"MIDI backend error: {exc}")
        self.port_combo["values"] = names
        if names and self.port_var.get() not in names:
            pro = next((x for x in names if "UNO" in x.upper()), names[0])
            self.port_var.set(pro)

    def toggle_connect(self) -> None:
        if self.inport is not None:
            self.inport.close()
            self.inport = None
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
            elif msg.type in ("start", "stop", "continue", "clock"):
                self.rx_queue.put(("transport", str(msg)))
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
                raw = str(payload).encode("ascii", errors="replace")
                self._append_event(self.model.add_bytes(raw, "MIDI TRANSPORT"))
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
        if self.inport is not None:
            self.inport.close()
        super().destroy()


if __name__ == "__main__":
    ProtocolLab().mainloop()
