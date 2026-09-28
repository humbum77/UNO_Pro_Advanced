#!/usr/bin/env python3
"""
UNO Synth Pro .unosyp 64-step sequencer decoder
================================================

Reverse-engineered from controlled .unosyp differentials.

CONFIRMED STRUCTURE FOR THE 1081-BYTE SEQUENCE-PRESERVING VARIANT
-----------------------------------------------------------------
File sequencer area:
    offset 297
    4 pages * 196 bytes
    16 steps/page
    64 steps total

Each 196-byte page:
    +0..+1     2-byte page header
    +2..+185   184-byte 7-bit packed sequence block
    +186..+195 10-byte page metadata (opaque/preserved)

The 184-byte sequence block contains 1288 stored bits.
Read every stored byte as a 7-bit value, LSB-first, concatenate the bits,
discard the first 6 padding bits, then read 160 bytes LSB-first:

    160 bytes = 16 steps * 10 bytes

Each decoded 10-byte step record:
    +0 control / flags byte          (semantic bits not fully mapped)
    +1 Note 1
    +2 Velocity 1
    +3 Extra 1                      (meaning not yet confirmed)
    +4 Note 2
    +5 Velocity 2
    +6 Extra 2
    +7 Note 3
    +8 Velocity 3
    +9 Extra 3

0xFF in a note slot means unused/empty voice.

This decoder is READ-ONLY. It does not modify presets or send MIDI/SysEx.
Unknown control bits, Extra fields, headers and metadata remain opaque.

The 1084-byte EMPTY/test5 variant produced by the official editor is
deliberately NOT treated as equivalent because controlled testing showed
the official editor can discard sequence data when re-saving a preset.

Usage:
    python unosyp_seq_decoder.py preset.unosyp
    python unosyp_seq_decoder.py preset.unosyp --all
    python unosyp_seq_decoder.py preset.unosyp --json
    python unosyp_seq_decoder.py preset.unosyp --raw
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

EXPECTED_SIZE = 1081
SEQ_START = 297
PAGE_COUNT = 4
PAGE_SIZE = 196
STEPS_PER_PAGE = 16
STEP_SIZE = 10

PAGE_HEADER_SIZE = 2
PACKED_SIZE = 184
PAGE_META_SIZE = 10
PACKED_PADDING_BITS = 6
RAW_PAGE_SIZE = 160

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B")


def midi_note_name(note: int) -> str:
    if not 0 <= note <= 127:
        return f"0x{note:02X}"
    return f"{NOTE_NAMES[note % 12]}{note // 12 - 1}"


def _bits_lsb7(data: bytes) -> List[int]:
    """Expand each stored byte to seven LSB-first bits."""
    bits: List[int] = []
    for b in data:
        value = b & 0x7F
        for bit in range(7):
            bits.append((value >> bit) & 1)
    return bits


def unpack_page_sequence(packed: bytes) -> bytes:
    """
    Decode the confirmed 184-byte page sequence representation.

    Algorithm established by controlled C4/C#4 / Step1/Step2 differentials:
      1. take 7 low bits from each file byte, LSB first;
      2. concatenate;
      3. discard first 6 pad bits;
      4. group next 1280 bits into 160 8-bit bytes, LSB first.
    """
    if len(packed) != PACKED_SIZE:
        raise ValueError(
            f"packed sequence must be {PACKED_SIZE} bytes, got {len(packed)}"
        )

    bits = _bits_lsb7(packed)
    bits = bits[PACKED_PADDING_BITS:]

    needed = RAW_PAGE_SIZE * 8
    if len(bits) < needed:
        raise ValueError("packed sequence is too short after padding")

    bits = bits[:needed]
    raw = bytearray()

    for i in range(0, needed, 8):
        value = 0
        for bit_index, bit in enumerate(bits[i:i + 8]):
            value |= bit << bit_index
        raw.append(value)

    return bytes(raw)


def decode_step_record(record: bytes, global_step: int) -> Dict[str, Any]:
    if len(record) != STEP_SIZE:
        raise ValueError(f"step record must be {STEP_SIZE} bytes")

    voices = []
    for voice in range(3):
        base = 1 + voice * 3
        note = record[base]
        velocity = record[base + 1]
        extra = record[base + 2]

        empty = note == 0xFF
        voices.append({
            "voice": voice + 1,
            "empty": empty,
            "note_raw": note,
            "note_name": None if empty else midi_note_name(note),
            "velocity": None if empty else velocity,
            "extra_raw": None if empty else extra,
        })

    active = [v for v in voices if not v["empty"]]

    return {
        "step": global_step,
        "control_raw": record[0],
        "record_hex": record.hex(" "),
        "active": bool(active),
        "notes": active,
        "voices": voices,
    }


def parse_page(page: bytes, page_index: int, file_offset: int) -> Dict[str, Any]:
    if len(page) != PAGE_SIZE:
        raise ValueError(f"page must be {PAGE_SIZE} bytes")

    header = page[:PAGE_HEADER_SIZE]
    packed = page[PAGE_HEADER_SIZE:PAGE_HEADER_SIZE + PACKED_SIZE]
    metadata = page[PAGE_HEADER_SIZE + PACKED_SIZE:]
    raw = unpack_page_sequence(packed)

    steps = []
    for local_step in range(STEPS_PER_PAGE):
        start = local_step * STEP_SIZE
        record = raw[start:start + STEP_SIZE]
        global_step = page_index * STEPS_PER_PAGE + local_step + 1
        steps.append(decode_step_record(record, global_step))

    return {
        "page": page_index + 1,
        "file_offset_start": file_offset,
        "file_offset_end": file_offset + PAGE_SIZE - 1,
        "header_hex": header.hex(" "),
        "packed_hex": packed.hex(" "),
        "metadata_hex": metadata.hex(" "),
        "raw_hex": raw.hex(" "),
        "steps": steps,
    }


def parse_unosyp(data: bytes) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "size": len(data),
        "expected_size": EXPECTED_SIZE,
        "supported_sequence_variant": len(data) == EXPECTED_SIZE,
        "sequence_start": SEQ_START,
        "pages": [],
    }

    if len(data) != EXPECTED_SIZE:
        result["warning"] = (
            f"Unsupported .unosyp variant: {len(data)} bytes. "
            f"The confirmed sequence-preserving test files are {EXPECTED_SIZE} bytes. "
            "No semantic sequencer decode was attempted."
        )
        return result

    required = SEQ_START + PAGE_COUNT * PAGE_SIZE
    if len(data) < required:
        result["warning"] = "File is truncated before the complete sequencer area."
        result["supported_sequence_variant"] = False
        return result

    for page_index in range(PAGE_COUNT):
        offset = SEQ_START + page_index * PAGE_SIZE
        page = data[offset:offset + PAGE_SIZE]
        result["pages"].append(parse_page(page, page_index, offset))

    result["steps"] = [
        step
        for page in result["pages"]
        for step in page["steps"]
    ]
    result["active_steps"] = [
        step["step"] for step in result["steps"] if step["active"]
    ]
    return result


def print_summary(info: Dict[str, Any], show_all: bool = False, show_raw: bool = False) -> None:
    print(f"File size: {info['size']} bytes")
    print(f"Supported sequence variant: {info['supported_sequence_variant']}")

    if not info["supported_sequence_variant"]:
        print(f"WARNING: {info.get('warning', 'unsupported variant')}")
        return

    print(f"Sequencer: 64 steps, 4 pages x 16")
    print("Active steps:", ", ".join(map(str, info["active_steps"])) or "none")

    for page in info["pages"]:
        print()
        print(
            f"PAGE {page['page']} "
            f"[{page['file_offset_start']}..{page['file_offset_end']}] "
            f"header={page['header_hex']} meta={page['metadata_hex']}"
        )

        if show_raw:
            print("raw:", page["raw_hex"])

        for step in page["steps"]:
            if not show_all and not step["active"]:
                continue

            note_text = []
            for n in step["notes"]:
                note_text.append(
                    f"V{n['voice']}={n['note_name']} "
                    f"(MIDI {n['note_raw']}), vel={n['velocity']}, extra={n['extra_raw']}"
                )

            payload = "; ".join(note_text) if note_text else "EMPTY"
            print(
                f"  Step {step['step']:02d}: "
                f"control=0x{step['control_raw']:02X} | {payload}"
            )

            if show_all:
                print(f"           raw={step['record_hex']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decode UNO Synth Pro .unosyp 64-step sequencer data"
    )
    parser.add_argument("file", type=Path)
    parser.add_argument(
        "--all", action="store_true",
        help="show empty as well as active steps"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="output machine-readable JSON"
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="also print raw 160-byte page payloads"
    )
    args = parser.parse_args()

    data = args.file.read_bytes()
    info = parse_unosyp(data)

    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print_summary(info, show_all=args.all, show_raw=args.raw)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
