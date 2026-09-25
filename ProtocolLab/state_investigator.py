"""State-diff helpers for UNO Synth Pro hardware experiments.

No guessed write commands live here. The investigator compares captured
0x37 replies and raw device traffic; F8 clock is deliberately excluded.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass

CLOCK=0xF8
STATE_CMD=0x37

def is_clock(data: bytes)->bool:
    return data == bytes([CLOCK])

def changed_bytes(before: bytes, after: bytes):
    if len(before)!=len(after):
        return []
    return [(i,a,b,a^b) for i,(a,b) in enumerate(zip(before,after)) if a!=b]

def changed_bits(before: bytes, after: bytes):
    out=[]
    for off,a,b,x in changed_bytes(before,after):
        for bit in range(8):
            mask=1<<bit
            if x & mask:
                out.append((off,mask,bool(a&mask),bool(b&mask)))
    return out

def stable_bit_changes(pairs):
    """Return bit transitions repeated in every same-direction capture pair."""
    pairs=list(pairs)
    if not pairs:return []
    sets=[]
    for a,b in pairs:
        sets.append(set(changed_bits(a,b)))
    return sorted(set.intersection(*sets), key=lambda x:(x[0],x[1]))

def unsolicited_signature(events):
    """Count non-clock raw packets so repeated physical-button traffic stands out."""
    return Counter(bytes(e) for e in events if e and not is_clock(bytes(e)))
