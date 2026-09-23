#!/usr/bin/env python3
"""Canonical read-only UNO Synth Pro Step Automation decoder.

Factory ``.unosyp`` files and hardware 0x29 pages share the same extension
grammar. Unknown patterns retain raw bytes; target names are never guessed.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

PAGE_OFFSET = 297
CORE_LENGTH = 192
MASTER_VALUES = (
    ("LEVEL1", "0b"), ("LEVEL2", "16"), ("LEVEL3", "21"),
    ("CUTOFF1", "006e"), ("RES1", "2c"), ("ENV1", "eb"),
    ("CUTOFF2", "00dd"), ("RES2", "37"), ("ENV2", "15"),
    ("SPACING", "e0"), ("LFO1", "04ce"), ("LFO2", "08fc"),
    ("DRIVE", "42"), ("MOD", "4d"), ("DELAY", "58"), ("REVERB", "63"),
)
MASTER_PAYLOAD = bytes.fromhex("".join(value for _, value in MASTER_VALUES))
MAX_ENTRIES_PER_STEP = 18
PARAMETERS = {
    "WAVE1": (2, False), "TUNE1": (2, True), "WAVE2": (2, False),
    "TUNE2": (2, True), "WAVE3": (2, False), "TUNE3": (2, True),
    "LEVEL1": (1, False), "LEVEL2": (1, False), "LEVEL3": (1, False),
    "CUTOFF1": (2, False), "RES1": (1, False), "ENV1": (1, True),
    "CUTOFF2": (2, False), "RES2": (1, False), "ENV2": (1, True),
    "SPACING": (1, True), "LFO1": (2, False), "LFO2": (2, False),
    "DRIVE": (1, False), "MOD": (1, False), "DELAY": (1, False),
    "REVERB": (1, False), "NOISE": (1, False),
}
SINGLE_VALUES = {
    "WAVE1": "0081", "TUNE1": "0032", "WAVE2": "0103", "TUNE2": "ffce",
    "WAVE3": "0182", "TUNE3": "0032", "LEVEL1": "0b", "LEVEL2": "16",
    "LEVEL3": "21", "CUTOFF1": "006e", "RES1": "2c", "ENV1": "eb",
    "CUTOFF2": "00dd", "RES2": "37", "ENV2": "15", "SPACING": "e0",
    "LFO1": "04ce", "LFO2": "08fc", "DRIVE": "42", "MOD": "4d",
    "DELAY": "58", "REVERB": "63", "NOISE": "40",
}
SINGLE_SELECTION = {
    "WAVE1": "1a", "TUNE1": "00", "WAVE2": "e0", "TUNE2": "a0",
    "WAVE3": "00", "TUNE3": "00", "LEVEL1": "00", "LEVEL2": "a0",
    "LEVEL3": "00", "CUTOFF1": "3e", "RES1": "50", "ENV1": "02",
    "CUTOFF2": "4c", "RES2": "00", "ENV2": "02", "SPACING": "00",
    "LFO1": "3e", "LFO2": "32", "DRIVE": "a0", "MOD": "a0",
    "DELAY": "00", "REVERB": "00", "NOISE": "1a",
}
CONTROLLED_PAIRS = (
    ("WAVE1_TUNE1", "9c", (("WAVE1", "0081"), ("TUNE1", "0032"))),
    ("TUNE1_WAVE2", "08", (("TUNE1", "0032"), ("WAVE2", "0103"))),
    ("WAVE2_TUNE2", "18", (("WAVE2", "0100"), ("TUNE2", "ffce"))),
    ("TUNE2_WAVE3", "44", (("TUNE2", "ffce"), ("WAVE3", "0183"))),
    ("WAVE3_TUNE3", "50", (("WAVE3", "0180"), ("TUNE3", "0032"))),
    ("TUNE3_LEVEL1", "00", (("TUNE3", "0032"), ("LEVEL1", "0b"))),
    ("LEVEL1_LEVEL2", "00", (("LEVEL1", "0b"), ("LEVEL2", "16"))),
    ("LEVEL2_LEVEL3", "20", (("LEVEL2", "16"), ("LEVEL3", "21"))),
    ("LEVEL3_CUTOFF1", "20", (("LEVEL3", "21"), ("CUTOFF1", "006e"))),
    ("CUTOFF1_RES1", "00", (("CUTOFF1", "006e"), ("RES1", "2c"))),
    ("RES1_ENV1", "88", (("RES1", "2c"), ("ENV1", "eb"))),
    ("ENV1_CUTOFF2", "00", (("ENV1", "eb"), ("CUTOFF2", "00dd"))),
    ("CUTOFF2_RES2", "00", (("CUTOFF2", "00dd"), ("RES2", "37"))),
    ("RES2_ENV2", "18", (("RES2", "37"), ("ENV2", "15"))),
    ("ENV2_SPACING", "00", (("ENV2", "15"), ("SPACING", "e0"))),
    ("SPACING_LFO1", "00", (("SPACING", "e0"), ("LFO1", "04ce"))),
    ("LFO1_LFO2", "00", (("LFO1", "04ce"), ("LFO2", "08fc"))),
    ("LFO2_DRIVE", "10", (("LFO2", "08fc"), ("DRIVE", "42"))),
    ("DRIVE_MOD", "50", (("DRIVE", "42"), ("MOD", "4d"))),
    ("MOD_DELAY", "00", (("MOD", "4d"), ("DELAY", "58"))),
    ("DELAY_REVERB", "0c", (("DELAY", "58"), ("REVERB", "63"))),
    ("REVERB_NOISE", "50", (("NOISE", "40"), ("REVERB", "63"))),
    ("GAP_WAVE1_NOISE", "00", (("WAVE1", "0081"), ("NOISE", "40"))),
    ("GAP_TUNE1_REVERB", "00", (("TUNE1", "0032"), ("REVERB", "63"))),
    ("GAP_LEVEL1_LEVEL3", "00", (("LEVEL1", "0b"), ("LEVEL3", "21"))),
    ("GAP_CUTOFF1_CUTOFF2", "00", (("CUTOFF1", "006e"), ("CUTOFF2", "00dd"))),
    ("GAP_RES1_RES2", "00", (("RES1", "2c"), ("RES2", "37"))),
    ("GAP_ENV1_ENV2", "00", (("ENV1", "eb"), ("ENV2", "15"))),
    ("GAP_DRIVE_DELAY", "00", (("DRIVE", "42"), ("DELAY", "58"))),
)
# These variants remove precisely one native value. The control bytes are
# included in the exact-match key, so coincidental matching cannot name lanes.
CLEAN_DROPS = {
    "CUTOFF1": "0000", "CUTOFF2": "0000", "DELAY": "0080",
    "DRIVE": "0000", "LFO1": "0000", "LFO2": "0080",
    "RES1": "0080", "RES2": "0000",
}
# In these files one target disappears, while another native value changes.
# The changes are captured explicitly and are not treated as a universal rule.
CAPTURE_VARIANTS = {
    "ENV1": ("0000", {"LEVEL3": "20", "REVERB": "62"}),
    "LEVEL1": ("0000", {"DRIVE": "41"}),
    "LEVEL2": ("0000", {"DRIVE": "41"}),
    "LEVEL3": ("0000", {"DRIVE": "41"}),
}


def unpack7(data: bytes) -> bytes:
    value = bits = 0
    out = bytearray()
    for byte in data:
        if byte > 127:
            raise ValueError("extension contains a byte outside 7-bit transport")
        value |= byte << bits
        bits += 7
        while bits >= 8:
            out.append(value & 255)
            value >>= 8
            bits -= 8
    if value:  # remaining padding bits must be zero
        raise ValueError("nonzero extension padding")
    return bytes(out)


def pages(data: bytes) -> list[dict]:
    if len(data) < PAGE_OFFSET:
        raise ValueError("file shorter than preset state")
    offset = PAGE_OFFSET
    result = []
    for index in range(4):
        if offset + 4 > len(data):
            raise ValueError(f"missing page {index + 1}")
        length = struct.unpack_from("<I", data, offset)[0]
        if length < CORE_LENGTH or offset + 4 + length > len(data):
            raise ValueError(f"invalid page {index + 1} length")
        start = offset + 4
        packed = data[start + CORE_LENGTH:start + length]
        result.append({"index": index + 1, "length": length,
                       "extension": unpack7(packed)})
        offset = start + length
    if offset != len(data):
        raise ValueError("unexpected trailing bytes")
    return result


def profile_map() -> dict[tuple[int, bytes, bytes], list[tuple[str, list[tuple[str, bytes]]]]]:
    result = {}
    def add(label: str, entries: list[tuple[str, str]], selection: str):
        raw = [(name, bytes.fromhex(value)) for name, value in entries]
        key = len(raw), bytes.fromhex(selection), b"".join(value for _, value in raw)
        result.setdefault(key, []).append((label, raw))
    add("MASTER", list(MASTER_VALUES), "0000")
    for name, value in SINGLE_VALUES.items():
        add(f"SINGLE_{name}", [(name, value)], SINGLE_SELECTION[name])
    for label, selection, entries in CONTROLLED_PAIRS:
        add(label, list(entries), selection)
    add("MASTER_7", [("WAVE1", "0082"), ("TUNE1", "0032"),
                     ("WAVE2", "0102"), ("TUNE2", "ffce"),
                     ("WAVE3", "0181"), ("TUNE3", "0032"),
                     ("NOISE", "40")], "00")
    add("SET_03", [("WAVE1", "0082"), ("TUNE1", "0032"),
                   ("WAVE2", "0103")], "00")
    add("SET_04", [("WAVE1", "0082"), ("TUNE1", "0032"),
                   ("WAVE2", "0103"), ("TUNE2", "ffce")], "00")
    add("THREE_WAVES", [("WAVE1", "0080"), ("WAVE2", "0100"),
                        ("WAVE3", "0182")], "40")
    for removed, selection in CLEAN_DROPS.items():
        add(f"DROP_{removed}", [(name, value) for name, value in MASTER_VALUES
                                if name != removed], selection)
    for removed, (selection, changes) in CAPTURE_VARIANTS.items():
        add(f"DROP_{removed}_WITH_VALUE_CHANGES",
            [(name, changes.get(name, value)) for name, value in MASTER_VALUES
             if name != removed], selection)
    return result


PROFILES = profile_map()


def _parse_record_stream(data: bytes, first_step: int, last_step: int) -> list[dict] | None:
    """Split a page-local stream into Step/Count/Selection/Values records.

    Native values are one or two bytes wide.  Record boundaries can therefore
    be recovered without guessing target names: a valid split must consume the
    stream exactly and every following header must name a step on this page.
    Ambiguous streams stay unresolved.
    """
    solutions: list[list[dict]] = []

    def visit(offset: int, records: list[dict]) -> None:
        if len(solutions) > 1:
            return
        if offset == len(data):
            solutions.append(records)
            return
        if offset + 3 > len(data):
            return
        step, count = data[offset:offset + 2]
        if not first_step <= step <= last_step or not 1 <= count <= MAX_ENTRIES_PER_STEP:
            return
        selection_length = (count + 7) // 8
        values_start = offset + 2 + selection_length
        if values_start > len(data):
            return
        # Every entry occupies either one or two native bytes.
        for values_length in range(count, count * 2 + 1):
            end = values_start + values_length
            if end > len(data):
                break
            visit(end, records + [{
                "step": step,
                "count": count,
                "selection": data[offset + 2:values_start],
                "payload": data[values_start:end],
            }])

    visit(0, [])
    return solutions[0] if len(solutions) == 1 else None


def _decode_page_records(parsed: list[dict]) -> list[dict] | None:
    """Decode the cumulative four-page automation representation.

    Page 1 contains its local records.  Every later page starts with the
    concatenated native values of all preceding records, followed by records
    for that page.  This is the layout used by factory presets with automation
    on several sequence steps.
    """
    records: list[dict] = []
    prior_values = b""
    for page_index, page in enumerate(parsed):
        extension = page["extension"]
        if not extension.startswith(prior_values):
            return None
        local = extension[len(prior_values):]
        page_records = _parse_record_stream(
            local, page_index * 16 + 1, page_index * 16 + 16
        )
        if page_records is None:
            return None
        records.extend(page_records)
        prior_values += b"".join(item["payload"] for item in page_records)
    return records


def _factory_cutoff1_entry(record: dict) -> dict | None:
    """Resolve the independently identified CUTOFF1 lane in FAKE 808 layout.

    The factory capture establishes that selection 90/98 starts with CUTOFF1.
    Its first native value is 16-bit and is followed by the remaining ordered
    values.  Restricting this rule to the observed selection/count/width shapes
    prevents it from naming unrelated unknown records.
    """
    payload = record["payload"]
    selection = record["selection"]
    count = record["count"]
    expected_lengths = {(0x98, 2): 3, (0x98, 3): 5,
                        (0x90, 2): 3, (0x90, 3): 5, (0x90, 4): 6}
    if len(selection) != 1 or expected_lengths.get((selection[0], count)) != len(payload):
        return None
    if len(payload) < 2:
        return None
    raw = payload[:2]
    value = int.from_bytes(raw, "big")
    if not 0 <= value <= 511:
        return None
    return {"name": "CUTOFF1", "native_hex": raw.hex(),
            "native_unsigned": value, "native_signed": None,
            "value": value + 1, "step": record["step"],
            "confidence": "validated factory multi-step layout"}


def decode(data: bytes) -> dict:
    try:
        document=json.loads(bytes(data).decode('utf-8-sig'))
    except (UnicodeDecodeError,json.JSONDecodeError):
        document=None
    if isinstance(document,dict) and isinstance(document.get('sequence'),dict):
        sequence=document['sequence'];steps=sequence.get('steps',[]);automation=sequence.get('automation',[])
        return {'format':'editor-json','status':'stored editor sequence','step':None,
                'count':len(automation) if isinstance(automation,list) else 0,
                'sequence_length':sequence.get('length'),'active_steps':[
                    index+1 for index,item in enumerate(steps)
                    if isinstance(item,dict) and item.get('notes')],
                'automation':automation if isinstance(automation,list) else [],
                'native_automation':sequence.get('native_automation',{})}
    parsed = pages(data)
    first = parsed[0]["extension"]
    if not first:
        return {"step": None, "count": 0, "selection_hex": "",
                "values_hex": "", "pages_match": all(not p["extension"] for p in parsed[1:]),
                "profile": None, "parameters": [], "status": "empty"}
    records = _decode_page_records(parsed)
    if records is not None and len(records) > 1:
        parameters = [entry for record in records
                      if (entry := _factory_cutoff1_entry(record)) is not None]
        return {
            "step": records[0]["step"], "count": sum(r["count"] for r in records),
            "selection_hex": records[0]["selection"].hex(),
            "values_hex": "".join(r["payload"].hex() for r in records),
            "page_values_hex": [p["extension"].hex() for p in parsed[1:]],
            "pages_match": False, "profile": "FACTORY_MULTI_STEP_CUTOFF1" if parameters else None,
            "parameters": parameters,
            "records": [{"step": r["step"], "count": r["count"],
                         "selection_hex": r["selection"].hex(),
                         "values_hex": r["payload"].hex()} for r in records],
            "status": ("decoded cumulative factory pages; CUTOFF1 resolved"
                       if parameters else "decoded cumulative factory pages; targets unresolved"),
        }
    if len(first) < 2:
        raise ValueError("incomplete step/count")
    step, count = first[:2]
    selection_length = (count + 7) // 8
    if len(first) < 2 + selection_length:
        raise ValueError("incomplete selection block")
    selection = first[2:2 + selection_length]
    payload = first[2 + selection_length:]
    mirrors = [p["extension"] for p in parsed[1:]]
    matches = all(ext == payload for ext in mirrors)
    result = {"step": step, "count": count, "selection_hex": selection.hex(),
              "values_hex": payload.hex(), "page_values_hex": [m.hex() for m in mirrors],
              "pages_match": matches, "profile": None, "parameters": [],
              "status": "unknown parameter selection"}
    if not matches:
        result["status"] = "pages differ; target resolution skipped"
        return result
    known = PROFILES.get((count, selection, payload), [])
    if len(known) == 1:
        label, entries = known[0]
        result["profile"] = label
        result["status"] = "exact match to 2026-09-22 capture profile"
        result["parameters"] = []
        for name, value in entries:
            width, signed = PARAMETERS[name]
            unsigned = int.from_bytes(value, "big")
            signed_value = int.from_bytes(value, "big", signed=True) if signed else None
            result["parameters"].append({
                "name": name, "native_hex": value.hex(), "native_width": width,
                "native_unsigned": unsigned, "native_signed": signed_value,
                "value": signed_value if signed else unsigned,
            })
    elif len(known) > 1:
        result["profile_candidates"] = [label for label, _ in known]
        result["status"] = "ambiguous exact capture match; targets left unresolved"
    return result


def decode_page_payloads(payloads) -> dict:
    """Decode Step Automation from four hardware/file page payloads.

    A payload is the complete length-prefixed `.unosyp` page body: the first
    192 bytes are the sequence core and the optional tail is the packed Step
    Automation extension.  This adapter deliberately calls :func:`decode`, so
    file and hardware reads cannot grow separate automation decoders.
    """
    payloads = [bytes(payload) for payload in payloads]
    if len(payloads) != 4:
        raise ValueError(f"expected four sequence pages, got {len(payloads)}")
    container = bytearray(PAGE_OFFSET)
    for index, payload in enumerate(payloads, 1):
        if len(payload) < CORE_LENGTH:
            raise ValueError(f"page {index} shorter than {CORE_LENGTH} bytes")
        container += struct.pack("<I", len(payload))
        container += payload
    return decode(bytes(container))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    for file in args.files:
        try:
            result = decode(file.read_bytes())
            result["file"] = str(file)
        except (OSError, ValueError) as exc:
            result = {"file": str(file), "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

