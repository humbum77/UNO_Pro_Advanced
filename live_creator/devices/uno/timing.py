"""Read-only timing. Binary length mapping confirmed by controlled captures.

Raw offsets 207..208: length=((lo | hi<<7)+1)//8. The user additionally
confirmed 1/16-note steps for this UNO format. Never infer length from notes.
"""
import json
from pathlib import Path

def decode_sequence_length(data):
    # Same 297-byte / 7-bit state framing as the inherited read-only decoder.
    if len(data)<297 or any(value>127 for value in data[1:297]):return None
    length=((data[207] | (data[208]<<7))+1)//8
    return length if 1<=length<=64 else None

def sequence_length(reference):
    if reference is None:return None
    try:
        raw=Path(reference).read_bytes()
        try:
            data=json.loads(raw.decode('utf-8-sig'));seq=data['sequence']
            length=seq['length']
            return length if type(length)is int and 1<=length<=64 and seq.get('length_confirmed') is True else None
        except (UnicodeError,ValueError):return decode_sequence_length(raw)
    except (OSError,KeyError,TypeError):return None

def sequence_beats(reference):
    if reference is None:return None  # EMPTY duration has no agreed musical unit.
    try:
        raw=Path(reference).read_bytes()
        try:data=json.loads(raw.decode('utf-8-sig'))
        except (UnicodeError,ValueError):
            length=decode_sequence_length(raw)
            return length/4 if length is not None else None
        seq=data['sequence'];length=seq['length'];resolution=seq['resolution']
        if seq.get('length_confirmed') is not True:return None
        if type(length)is not int or not 1<=length<=64:return None
        divisions={'1/1':4.,'1/2':2.,'1/4':1.,'1/8':.5,'1/16':.25,'1/32':.125,'1/64':.0625}
        if seq.get('timing','STRAIGHT')!='STRAIGHT':return None
        return length*divisions[resolution]
    except (OSError,UnicodeError,ValueError,KeyError,TypeError):return None
