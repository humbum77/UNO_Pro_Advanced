"""Read-only UNO Synth Pro .unosyp preset-state decoder.

Confirmed by structural equivalence with the real-hardware 0x37 state mapper:
- file byte 0 is raw state byte 0;
- file bytes 1..296 are a continuous 7-bit LSB-first stream containing
  raw state bytes 1..259 (296*7 == 259*8);
- the resulting 260-byte raw state can be wrapped with the same six-bit
  prefix packing used by the 309-byte 0x37 reply and decoded by the existing
  exact-observed hardware LUT.

No write/store protocol is implemented here.
"""
from pathlib import Path

FILE_STATE_SIZE = 297
RAW_STATE_SIZE = 260
STATE_PACKED_SIZE = 298
IK_STATE_PREFIX = bytes((0xF0,0x00,0x21,0x1A,0x02,0x03,0x00,0x37,0x00,0x00))


def _unpack_7bit_continuous(data: bytes) -> bytes:
    bits=[]
    for value in data:
        if value > 0x7F:
            raise ValueError('not a 7-bit .unosyp stream')
        bits.extend((value >> i) & 1 for i in range(7))
    if len(bits) % 8:
        raise ValueError('7-bit stream does not contain a whole number of bytes')
    out=bytearray()
    for pos in range(0,len(bits),8):
        value=0
        for bit in range(8):
            value |= bits[pos+bit] << bit
        out.append(value)
    return bytes(out)


def decode_file_state_raw(data: bytes) -> bytes:
    """Return the 260-byte preset state embedded at the start of a .unosyp."""
    data=bytes(data)
    if len(data) < FILE_STATE_SIZE:
        raise ValueError(f'.unosyp too short for preset state: {len(data)}')
    tail=_unpack_7bit_continuous(data[1:FILE_STATE_SIZE])
    raw=bytes((data[0],))+tail
    if len(raw) != RAW_STATE_SIZE:
        raise AssertionError(f'unexpected raw state length: {len(raw)}')
    return raw


def encode_raw_as_0x37_payload(raw: bytes) -> bytes:
    """Pack 260 raw bytes exactly as the 298-byte payload of a 0x37 reply."""
    raw=bytes(raw)
    if len(raw) != RAW_STATE_SIZE:
        raise ValueError(f'expected {RAW_STATE_SIZE} raw bytes, got {len(raw)}')
    bits=[0]*6
    for value in raw:
        bits.extend((value >> i) & 1 for i in range(8))
    out=bytearray()
    for pos in range(0,len(bits),7):
        chunk=bits[pos:pos+7]
        if len(chunk) != 7:
            raise AssertionError('0x37 payload packing alignment error')
        out.append(sum(bit << i for i,bit in enumerate(chunk)))
    if len(out) != STATE_PACKED_SIZE:
        raise AssertionError(f'unexpected packed state length: {len(out)}')
    return bytes(out)


def decode_0x37_raw(frame: bytes) -> bytes:
    frame=bytes(frame)
    if len(frame)!=309 or frame[:10]!=IK_STATE_PREFIX or frame[-1]!=0xF7:
        raise ValueError('expected UNO 309-byte 0x37 state frame')
    bits=[]
    for value in frame[10:-1]:
        bits.extend((value >> i) & 1 for i in range(7))
    bits=bits[6:6+RAW_STATE_SIZE*8]
    out=bytearray()
    for pos in range(0,len(bits),8):
        out.append(sum(bits[pos+i] << i for i in range(8)))
    if len(out)!=RAW_STATE_SIZE:
        raise AssertionError(f'unexpected raw state length: {len(out)}')
    return bytes(out)

def build_virtual_0x37(data: bytes) -> bytes:
    """Build a read-only synthetic 309-byte 0x37 frame from .unosyp state bytes."""
    raw=decode_file_state_raw(data)
    return IK_STATE_PREFIX + encode_raw_as_0x37_payload(raw) + bytes((0xF7,))



def _get_bits(raw: bytes, start_bit: int, count: int) -> int:
    value=0
    for i in range(count):
        pos=start_bit+i
        value |= ((raw[pos//8] >> (pos%8)) & 1) << i
    return value

def decode_extended_preset_fields(raw: bytes):
    """Decode non-CC preset fields confirmed by controlled ARP captures.

    2026-09-10 hardware differentials establish:
    - ARP Direction: 4 bits starting at raw byte177 bit5; values 0..9.
    - ARP Range: 3 bits starting at raw byte178 bit5; values 1..4.
    - ARP Pattern occupies the next 16 contiguous bits starting at byte179 bit5.
      The field location/width is confirmed by all-on -> all-off state captures.
      A non-symmetric capture establishes byte order versus 3E 00 02; after
      16-bit byte swap, logical bit 0..15 maps to ARP step 1..16.
    """
    raw=bytes(raw)
    if len(raw)!=RAW_STATE_SIZE:
        raise ValueError(f'expected {RAW_STATE_SIZE} raw bytes, got {len(raw)}')
    # Voice Mode confirmed by 2026-09-11 controlled hardware capture
    # MONO -> LEGATO -> PARA -> MONO. The field is raw byte 175 bits 5..6
    # and encodes the three modes as 0/1/2. Read-side only.
    voice_mode=(raw[175] >> 5) & 0x03

    direction=_get_bits(raw,177*8+5,4)
    arp_range=_get_bits(raw,178*8+5,3)
    pattern_raw=_get_bits(raw,179*8+5,16)
    # One non-symmetric controlled capture confirms the state field is byte-swapped
    # relative to the 3E 00 02 16-bit logical step mask: 0x1101 -> 0x0111.
    pattern=((pattern_raw & 0xFF) << 8) | ((pattern_raw >> 8) & 0xFF)
    out={}
    if 0 <= voice_mode <= 2: out['voice_mode']=voice_mode
    if 0 <= direction <= 9: out['arp_direction']=direction
    if 1 <= arp_range <= 4: out['arp_range']=arp_range
    out['arp_pattern_raw']=pattern_raw
    out['arp_pattern']=pattern

    # Mod Matrix is a 16-route packed bitstream beginning at raw byte 188.
    # Hardware CC66..81 sweeps confirm a strict 32-bit stride for Amount:
    #   destination = bits 5..10 of the current 32-bit chunk (6 bits)
    #   fade_raw    = bits 11..20 (10 bits; semantic scale still unconfirmed)
    #   amount_raw  = bits 21..28 (8-bit signed-style stored value)
    #   source      = bits 29..31 of this chunk + bits 0..4 of the NEXT chunk.
    # The cross-chunk Source packing is independently validated against factory
    # slot 59 in USP_Presets.dfu: all four non-empty routes reproduce the exact
    # flash [destination, *, amount, source] bytes (27/0/14/1, 41/0/31/2,
    # 32/0/10/17, 29/0/18/0). Read-side only; no guessed write protocol.
    matrix=[]
    for slot in range(16):
        base=188+slot*4
        word=int.from_bytes(raw[base:base+4],'little')
        next_low5=raw[base+4] & 0x1F if base+4 < len(raw) else 0
        source=((word >> 29) & 0x07) | (next_low5 << 3)
        destination=(word >> 5) & 0x3F
        fade_raw=(word >> 11) & 0x03FF
        amount_raw=(word >> 21) & 0xFF
        matrix.append({
            'source':source if source < 30 else None,
            'destination':destination if destination < 50 else None,
            'fade_raw':fade_raw,
            'amount_raw':amount_raw,
            'word':word,
        })
    out['matrix']=matrix
    return out

def decode_unosyp_state(path_or_bytes):
    """Decode .unosyp synth state through the exact hardware-observed 0x37 LUT."""
    from state_decoder import decode_state_0x37
    data=(Path(path_or_bytes).read_bytes() if isinstance(path_or_bytes,(str,Path)) else bytes(path_or_bytes))
    raw=decode_file_state_raw(data)
    frame=IK_STATE_PREFIX + encode_raw_as_0x37_payload(raw) + bytes((0xF7,))
    resolved,unresolved=decode_state_0x37(frame)
    return {'raw':raw,'frame':frame,'resolved':resolved,'unresolved':unresolved,'extended':decode_extended_preset_fields(raw)}
