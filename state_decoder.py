"""Exact-observed decoder for UNO Synth Pro 0x37 current-state replies.

Generated from the hardware FULL STATE MAPPER 128-point sweeps.
Only exact signatures observed on real hardware are returned.  There is no
nearest-value or guessed fallback: an unseen signature is reported unresolved.
"""
from pathlib import Path
import json

_MAP_PATH=Path(__file__).with_name('state_decoder_map.json')
with _MAP_PATH.open('r',encoding='utf-8') as _f:
    _DOC=json.load(_f)
FIELDS={int(k):v for k,v in _DOC['fields'].items()}

def _signature(data,field):
    return ':'.join(f"{(data[o] & m):02X}" for o,m in zip(field['offsets'],field['masks']))

def decode_state_0x37(data):
    """Return (resolved, unresolved_ccs) for an exact 309-byte state reply.

    resolved maps CC -> {ordinal, cc_min, cc_max, unique_states}.  The cc_min
    value is a safe CC-space representative of the observed hardware state;
    enum/toggle consumers should prefer ordinal.
    """
    data=bytes(data)
    resolved={}; unresolved=[]
    if len(data)!=309:
        return resolved,list(FIELDS)
    for cc,field in FIELDS.items():
        hit=field['lut'].get(_signature(data,field))
        if hit is None:
            unresolved.append(cc);continue
        resolved[cc]={**hit,'unique_states':field['unique_states']}
    return resolved,unresolved
