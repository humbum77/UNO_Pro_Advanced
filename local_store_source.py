"""Prepare a complete local .unosyp file for the existing hardware STORE flow.

This module only validates and prepares bytes. It never transmits MIDI.
"""
from pathlib import Path
import json
import struct

from unosyp_state_decoder import build_virtual_0x37
from unosyp_state_decoder import encode_0x37_as_file_state

IK_HEADER=bytes((0xF0,0x00,0x21,0x1A,0x02,0x03))


def build_current_buffer_load(path):
    """Build the confirmed non-STORE 0x36 current-buffer load for a binary preset."""
    data=Path(path).read_bytes()
    if len(data)<0x129 or data[:4]!=bytes((0x25,0x01,0x00,0x00)):
        raise ValueError('Local .unosyp has an unsupported state header')
    payload=data[4:0x129]
    if len(payload)!=0x125 or any(byte>0x7f for byte in payload):
        raise ValueError('Local .unosyp current-buffer state is incomplete')
    return IK_HEADER+bytes((0x36,0x00,0x60))+payload+bytes((0xF7,))


def prepare_local_store(path):
    source = Path(path)
    data = source.read_bytes()
    if data[:1] == b'{':
        try:
            obj = json.loads(data.decode('utf-8-sig'))
            raw_hex = obj.get('sequence', {}).get('native_raw_hex', '')
            data = bytes.fromhex(raw_hex)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError('Local preset has no valid complete binary .unosyp source') from exc
        if not data:
            raise ValueError('Local preset has no complete binary .unosyp source')
    if len(data) < 297 + 4 * (4 + 192):
        raise ValueError('Local .unosyp is too short for four complete sequence pages')
    if data[:4] != bytes((0x25, 0x01, 0x00, 0x00)):
        raise ValueError('Local .unosyp has an unsupported state header')
    state = build_virtual_0x37(data)
    pages = {}
    offset = 297
    for index in range(1, 5):
        if offset + 4 > len(data):
            raise ValueError(f'Local .unosyp page {index} has no length header')
        length = struct.unpack_from('<I', data, offset)[0]
        offset += 4
        if length < 192 or length > 65535 or offset + length > len(data):
            raise ValueError(f'Local .unosyp page {index} is incomplete')
        payload = data[offset:offset + length]
        if any(byte > 127 for byte in payload):
            raise ValueError(f'Local .unosyp page {index} is not SysEx-safe')
        pages[index] = payload
        offset += length
    if offset != len(data):
        raise ValueError('Local .unosyp has trailing bytes after page 4')
    return state, pages, source.stem

def build_local_unosyp(state, pages):
    """Build a native binary .unosyp from one 0x37 state and 0x29 pages."""
    prefix=encode_0x37_as_file_state(state);pages={int(k):bytes(v) for k,v in pages.items()}
    if 0 in pages and pages[0]!=prefix[4:297]:
        raise ValueError('0x37 state and hardware page 0 do not describe the same preset')
    body=bytearray(prefix)
    for page in range(1,5):
        payload=pages.get(page)
        if payload is None or len(payload)<192:raise ValueError(f'Hardware page {page} is incomplete')
        body.extend(struct.pack('<I',len(payload)));body.extend(payload)
    return bytes(body)
