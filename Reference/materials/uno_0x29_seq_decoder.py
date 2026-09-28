#!/usr/bin/env python3
"""
UNO Synth Pro SysEx 0x29 hardware-preset / sequencer decoder
============================================================

Purpose
-------
Decode the four 192-byte sequencer page payloads returned by the UNO Synth Pro
for the official hardware-preset read command:

    Request:
      F0 00 21 1A 02 03 29 00 00 <page> F7

    Response:
      F0 00 21 1A 02 03 00 29 00 00 <page> <payload> F7

Pages:
    0 = 293-byte main preset payload (not decoded here)
    1..4 = 192-byte sequencer pages

Confirmed 0x29 sequence-page layout
-----------------------------------
Each sequencer page is 192 bytes:

    +0..+181   182 bytes of 7-bit packed sequence data
    +182..191  10 bytes page metadata

The 182 packed bytes contain 1274 stored bits. The first 1272 bits decode to
159 raw sequence bytes. These are raw page bytes 1..159 of a 160-byte page:

    16 steps * 10 bytes = 160 bytes/page

The only raw byte not directly present in the packed stream is byte 0 of each
page: the 6-bit control field of local Step 1 (global Steps 1/17/33/49).

Therefore this decoder does NOT invent those four control values. They are
reported as None / unknown.

All remaining sequence bytes are recovered exactly:
    - Note 1/2/3
    - Velocity 1/2/3
    - Extra 1/2/3
    - control bytes for the other 60 steps

A note slot of 0xFF is unused.

Metadata
--------
The 10 metadata bytes are preserved verbatim.

Evidence-supported active bitmap mapping:
    metadata[1] bits 0..6 -> local Steps 2..8
    metadata[2] bits 0..6 -> local Steps 9..15

The following is exposed only as a candidate, not as confirmed truth:
    metadata[0] bit 6 -> local Step 1 active/data-present candidate

Local Step 16 active-bit mapping is unresolved.

Usage
-----
Decode a monitor capture:
    python uno_0x29_seq_decoder.py to_lib_preset001.txt

Show all steps:
    python uno_0x29_seq_decoder.py to_lib_preset001.txt --all

JSON:
    python uno_0x29_seq_decoder.py to_lib_preset001.txt --json

Compare recovered bytes against a 640-byte DFU sequence block:
    python uno_0x29_seq_decoder.py to_lib_preset001.txt \
        --flash preset1_sequence.bin

This script is READ-ONLY. It sends no MIDI/SysEx and modifies no hardware.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SYSEX_PREFIX_REQUEST = bytes([0xF0, 0x00, 0x21, 0x1A, 0x02, 0x03, 0x29, 0x00, 0x00])
SYSEX_RESPONSE_HEAD = bytes([0xF0, 0x00, 0x21, 0x1A, 0x02, 0x03, 0x00, 0x29, 0x00, 0x00])

SEQ_PAGE_COUNT = 4
SEQ_PAGE_PAYLOAD_SIZE = 192
PACKED_SIZE = 182
META_SIZE = 10
RAW_PAGE_SIZE = 160
STEPS_PER_PAGE = 16
STEP_SIZE = 10
RECOVERED_RAW_BYTES_PER_PAGE = 159

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B")


def midi_note_name(note: int) -> str:
    if not 0 <= note <= 127:
        return f"0x{note:02X}"
    return f"{NOTE_NAMES[note % 12]}{note // 12 - 1}"


def bits_lsb7(data: bytes) -> List[int]:
    bits: List[int] = []
    for b in data:
        v = b & 0x7F
        for bit in range(7):
            bits.append((v >> bit) & 1)
    return bits


def bits_to_bytes_lsb(bits: List[int]) -> bytes:
    if len(bits) % 8:
        raise ValueError("bit count must be divisible by 8")
    out = bytearray()
    for pos in range(0, len(bits), 8):
        value = 0
        for bit_index, bit in enumerate(bits[pos:pos + 8]):
            value |= (bit & 1) << bit_index
        out.append(value)
    return bytes(out)


def unpack_0x29_sequence_tail(packed: bytes) -> bytes:
    """
    Recover raw page bytes 1..159.

    182 * 7 = 1274 bits.
    The first 1272 bits are 159 complete raw bytes.
    The final 2 bits are not used for the recovered 159-byte raw tail.
    """
    if len(packed) != PACKED_SIZE:
        raise ValueError(f"packed page must be {PACKED_SIZE} bytes, got {len(packed)}")

    bits = bits_lsb7(packed)
    needed = RECOVERED_RAW_BYTES_PER_PAGE * 8  # 1272
    return bits_to_bytes_lsb(bits[:needed])


def decode_voice(record: List[Optional[int]], voice: int) -> Dict[str, Any]:
    base = 1 + voice * 3
    note = record[base]
    velocity = record[base + 1]
    extra = record[base + 2]

    # note/velocity/extra are always known even for the first step of a page.
    assert note is not None
    assert velocity is not None
    assert extra is not None

    empty = note == 0xFF
    return {
        "voice": voice + 1,
        "empty": empty,
        "note_raw": note,
        "note_name": None if empty else midi_note_name(note),
        "velocity": None if empty else velocity,
        "extra_raw": None if empty else extra,
    }


def decode_metadata(metadata: bytes) -> Dict[str, Any]:
    if len(metadata) != META_SIZE:
        raise ValueError(f"metadata must be {META_SIZE} bytes")

    # Evidence-supported mapping for local Steps 2..15.
    active_2_8 = {
        local_step: bool(metadata[1] & (1 << (local_step - 2)))
        for local_step in range(2, 9)
    }
    active_9_15 = {
        local_step: bool(metadata[2] & (1 << (local_step - 9)))
        for local_step in range(9, 16)
    }

    return {
        "raw_hex": metadata.hex(" "),
        "raw_bytes": list(metadata),
        "active_local_steps_2_15": {
            **active_2_8,
            **active_9_15,
        },
        "step1_active_candidate": bool(metadata[0] & 0x40),
        "step1_active_candidate_source": "metadata[0] bit6; strong candidate, not final mapping",
        "step16_active": None,
        "step16_active_source": "unresolved",
    }


def parse_0x29_page(payload: bytes, page_number: int) -> Dict[str, Any]:
    if page_number not in range(1, 5):
        raise ValueError("sequence page number must be 1..4")
    if len(payload) != SEQ_PAGE_PAYLOAD_SIZE:
        raise ValueError(
            f"0x29 sequence payload must be {SEQ_PAGE_PAYLOAD_SIZE} bytes, got {len(payload)}"
        )

    packed = payload[:PACKED_SIZE]
    metadata = payload[PACKED_SIZE:]
    tail = unpack_0x29_sequence_tail(packed)

    # Build a 160-byte logical page. Byte 0 is unknown; bytes 1..159 are exact.
    logical: List[Optional[int]] = [None] + list(tail)
    meta_info = decode_metadata(metadata)

    steps = []
    for local_idx in range(STEPS_PER_PAGE):
        start = local_idx * STEP_SIZE
        record = logical[start:start + STEP_SIZE]
        global_step = (page_number - 1) * STEPS_PER_PAGE + local_idx + 1

        voices = [decode_voice(record, v) for v in range(3)]
        active_notes = [v for v in voices if not v["empty"]]

        local_step = local_idx + 1
        if local_step == 1:
            data_active = meta_info["step1_active_candidate"]
            data_active_confidence = "candidate"
        elif 2 <= local_step <= 15:
            data_active = meta_info["active_local_steps_2_15"][local_step]
            data_active_confidence = "mapped"
        else:
            data_active = None
            data_active_confidence = "unknown"

        control = record[0]

        steps.append({
            "step": global_step,
            "page": page_number,
            "local_step": local_step,
            "control_raw": control,
            "control_known": control is not None,
            "control_note": (
                None if control is not None
                else "0x29 omits the first 6-bit control field of each 16-step page"
            ),
            "note_active": bool(active_notes),
            "data_active": data_active,
            "data_active_confidence": data_active_confidence,
            "notes": active_notes,
            "voices": voices,
            "record_hex": " ".join("??" if b is None else f"{b:02X}" for b in record),
        })

    return {
        "page": page_number,
        "payload_size": len(payload),
        "packed_hex": packed.hex(" "),
        "metadata": meta_info,
        "recovered_raw_tail_size": len(tail),
        "recovered_raw_tail_hex": tail.hex(" "),
        "unknown_raw_page_byte": 0,
        "steps": steps,
    }


def parse_monitor_capture(path: Path) -> Dict[int, bytes]:
    """
    Extract UNO→EDITOR SysEx 0x29 responses from UNO MIDI Monitor TSV capture.
    """
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    pages: Dict[int, bytes] = {}

    for line in text.splitlines():
        cols = line.split("\t")
        if len(cols) < 6:
            continue
        if cols[2] != "UNO→EDITOR" or cols[3] != "SysEx":
            continue

        try:
            msg = bytes(int(x, 16) for x in cols[5].split())
        except (ValueError, IndexError):
            continue

        if len(msg) < 12:
            continue
        if not msg.startswith(SYSEX_RESPONSE_HEAD):
            continue
        if msg[-1] != 0xF7:
            continue

        page = msg[10]
        payload = msg[11:-1]
        pages[page] = payload

    return pages


def compare_with_flash(decoded_pages: List[Dict[str, Any]], flash: bytes) -> Dict[str, Any]:
    if len(flash) != SEQ_PAGE_COUNT * RAW_PAGE_SIZE:
        raise ValueError(
            f"flash sequence must be exactly {SEQ_PAGE_COUNT * RAW_PAGE_SIZE} bytes, "
            f"got {len(flash)}"
        )

    known_total = 0
    known_match = 0
    mismatches: List[Dict[str, Any]] = []
    unknown_offsets: List[int] = []

    for page_idx, page in enumerate(decoded_pages):
        # Rebuild logical page from the per-step records.
        logical: List[Optional[int]] = []
        for step in page["steps"]:
            parts = step["record_hex"].split()
            logical.extend(None if x == "??" else int(x, 16) for x in parts)

        base = page_idx * RAW_PAGE_SIZE
        for rel, value in enumerate(logical):
            absolute = base + rel
            if value is None:
                unknown_offsets.append(absolute)
                continue
            known_total += 1
            if value == flash[absolute]:
                known_match += 1
            else:
                mismatches.append({
                    "offset": absolute,
                    "page": page_idx + 1,
                    "page_offset": rel,
                    "decoded": value,
                    "flash": flash[absolute],
                })

    return {
        "flash_size": len(flash),
        "known_bytes_compared": known_total,
        "known_bytes_matching": known_match,
        "known_bytes_mismatching": len(mismatches),
        "unknown_offsets": unknown_offsets,
        "mismatches": mismatches,
        "full_known_match": known_total == known_match,
    }


def decode_capture(path: Path) -> Dict[str, Any]:
    found = parse_monitor_capture(path)

    result: Dict[str, Any] = {
        "source": str(path),
        "command": "0x29",
        "main_page_0_size": len(found[0]) if 0 in found else None,
        "found_pages": {str(k): len(v) for k, v in sorted(found.items())},
        "sequence_pages": [],
    }

    missing = [p for p in range(1, 5) if p not in found]
    if missing:
        result["warning"] = f"missing sequence pages: {missing}"
        return result

    pages = [parse_0x29_page(found[p], p) for p in range(1, 5)]
    result["sequence_pages"] = pages
    result["steps"] = [step for page in pages for step in page["steps"]]
    result["note_active_steps"] = [
        step["step"] for step in result["steps"] if step["note_active"]
    ]
    result["control_unknown_steps"] = [
        step["step"] for step in result["steps"] if not step["control_known"]
    ]
    return result


def print_summary(info: Dict[str, Any], show_all: bool = False) -> None:
    print("UNO Synth Pro SysEx 0x29 sequence decoder")
    print(f"Source: {info['source']}")
    print(f"Found 0x29 pages: {info['found_pages']}")

    if "warning" in info:
        print("WARNING:", info["warning"])
        return

    print("Sequence: 64 steps / 4 pages")
    print("Note-active steps:",
          ", ".join(map(str, info["note_active_steps"])) or "none")
    print("Unknown control steps:",
          ", ".join(map(str, info["control_unknown_steps"])))

    for page in info["sequence_pages"]:
        md = page["metadata"]
        print()
        print(
            f"PAGE {page['page']}: metadata={md['raw_hex']} "
            f"| recovered raw bytes 1..159 = {page['recovered_raw_tail_size']}"
        )
        print(
            f"  Step1 active candidate={md['step1_active_candidate']} "
            f"| Step16 active=unknown"
        )

        for step in page["steps"]:
            if not show_all and not step["note_active"] and step["data_active"] is not True:
                continue

            notes = []
            for n in step["notes"]:
                notes.append(
                    f"V{n['voice']}={n['note_name']} "
                    f"(MIDI {n['note_raw']}), vel={n['velocity']}, extra={n['extra_raw']}"
                )
            note_text = "; ".join(notes) if notes else "NO NOTES"

            control = (
                f"0x{step['control_raw']:02X}"
                if step["control_known"]
                else "UNKNOWN"
            )

            print(
                f"  Step {step['step']:02d}: "
                f"control={control} | "
                f"data_active={step['data_active']} "
                f"({step['data_active_confidence']}) | "
                f"{note_text}"
            )

            if show_all:
                print(f"           raw={step['record_hex']}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Decode UNO Synth Pro hardware sequencer data from SysEx 0x29 monitor capture"
    )
    ap.add_argument("capture", type=Path, help="UNO MIDI Monitor TSV capture")
    ap.add_argument("--all", action="store_true", help="show all 64 steps")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument(
        "--flash", type=Path,
        help="optional 640-byte DFU/raw sequence block for byte-for-byte verification"
    )
    args = ap.parse_args()

    info = decode_capture(args.capture)

    if args.flash and "warning" not in info:
        flash = args.flash.read_bytes()
        info["flash_comparison"] = compare_with_flash(
            info["sequence_pages"], flash
        )

    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print_summary(info, show_all=args.all)
        if "flash_comparison" in info:
            c = info["flash_comparison"]
            print()
            print("FLASH COMPARISON")
            print(
                f"Known bytes: {c['known_bytes_matching']}/"
                f"{c['known_bytes_compared']} match"
            )
            print("Unknown raw offsets:", c["unknown_offsets"])
            if c["mismatches"]:
                print("Mismatches:")
                for m in c["mismatches"]:
                    print(
                        f"  offset {m['offset']}: "
                        f"decoded=0x{m['decoded']:02X}, flash=0x{m['flash']:02X}"
                    )
            else:
                print("No mismatches among all recoverable bytes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
