#!/usr/bin/env python3
"""Read-only UNO Synth Pro .unosyp structure probe.

This module reports only structure supported by project evidence. It never
rewrites a preset and never infers unknown automation parameter semantics.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

BINARY_MAGIC = bytes.fromhex("25 01 00 00")
AUTOMATION_COUNT_OFFSET = 494
AUTOMATION_RESERVED_OFFSET = 495
AUTOMATION_PAYLOAD_OFFSET = 496


@dataclass(frozen=True)
class UnosypProbe:
    path: str
    size: int
    binary_pro_format: bool
    automation_byte_count: int | None
    automation_reserved_byte: int | None
    automation_payload_hex: str
    automation_entries_hex: tuple[str, ...]
    trailing_offset: int | None


def probe_bytes(data: bytes, path: str = "<memory>") -> UnosypProbe:
    is_binary = data.startswith(BINARY_MAGIC)
    if not is_binary or len(data) <= AUTOMATION_RESERVED_OFFSET:
        return UnosypProbe(path, len(data), is_binary, None, None, "", (), None)

    count = data[AUTOMATION_COUNT_OFFSET]
    reserved = data[AUTOMATION_RESERVED_OFFSET]
    end = min(len(data), AUTOMATION_PAYLOAD_OFFSET + count)
    payload = data[AUTOMATION_PAYLOAD_OFFSET:end]
    # Project evidence says entries are two bytes; preserve odd trailing byte
    # rather than inventing its meaning.
    entries = tuple(
        payload[i:i + 2].hex(" ").upper()
        for i in range(0, len(payload), 2)
    )
    return UnosypProbe(
        path=path,
        size=len(data),
        binary_pro_format=True,
        automation_byte_count=count,
        automation_reserved_byte=reserved,
        automation_payload_hex=payload.hex(" ").upper(),
        automation_entries_hex=entries,
        trailing_offset=end,
    )


def probe_file(path: Path) -> UnosypProbe:
    return probe_bytes(path.read_bytes(), str(path))


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only UNO Synth Pro .unosyp structure probe")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true", dest="as_json")
    ns = ap.parse_args()

    rows = [probe_file(p) for p in ns.files]
    if ns.as_json:
        print(json.dumps([asdict(x) for x in rows], indent=2, ensure_ascii=False))
        return 0

    for row in rows:
        print(f"{row.path}: size={row.size} binary_pro={row.binary_pro_format}")
        if row.automation_byte_count is None:
            print("  automation: unavailable/not binary Pro format")
            continue
        print(f"  byte494/count={row.automation_byte_count} byte495=0x{row.automation_reserved_byte:02X}")
        print(f"  payload@496={row.automation_payload_hex or '<empty>'}")
        for i, entry in enumerate(row.automation_entries_hex):
            print(f"    entry[{i:02d}] raw={entry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
