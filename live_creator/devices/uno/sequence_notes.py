"""Read-only sequence-note preview for Live Creator clips.

JSON presets use their explicit sequence steps. Official 1081-byte presets use
the confirmed four-page, three-voice decoder. Unsupported variants return no
preview and are never modified.
"""
import json
from pathlib import Path
from .timing import decode_sequence_length

SEQ_START=297
PAGE_SIZE=196
PACKED_SIZE=184
PADDING_BITS=6

def _clean_notes(values):
    if not isinstance(values,(list,tuple)):return ()
    result=[]
    for value in values[:3]:
        try:value=int(value)
        except (TypeError,ValueError):continue
        if 0<=value<=127:result.append(value)
    return tuple(result)

def _json_preview(raw):
    data=json.loads(raw.decode('utf-8-sig'));seq=data.get('sequence',{})
    length=seq.get('length',0);steps=seq.get('steps',[])
    if type(length)is not int or not 1<=length<=64 or not isinstance(steps,list):return ()
    return tuple(_clean_notes(step.get('notes',())) if isinstance(step,dict) else () for step in steps[:length])+((),)*max(0,length-len(steps))

def _unpack_page(packed):
    if len(packed)!=PACKED_SIZE:return b''
    bits=[(byte>>bit)&1 for byte in packed for bit in range(7)][PADDING_BITS:PADDING_BITS+1280]
    if len(bits)!=1280:return b''
    return bytes(sum(bit<<offset for offset,bit in enumerate(bits[i:i+8])) for i in range(0,1280,8))

def _binary_preview(raw):
    try:
        from .unosyp_seq_decoder import parse_unosyp
        info=parse_unosyp(raw)
    except Exception:return ()
    if not info.get('supported_sequence_variant'):return ()
    length=info.get('sequence_length')
    if not isinstance(length,int) or not 1<=length<=64:return ()
    result=[]
    for item in info.get('steps',[])[:length]:
        notes=[]
        for voice in item.get('voices',[]):
            if not voice.get('empty') and 0<=int(voice.get('note_raw',-1))<=127:notes.append(int(voice['note_raw']))
        result.append(tuple(notes))
    return tuple(result)+((),)*max(0,length-len(result))

def read_sequence_notes(reference):
    if reference is None:return ()
    try:raw=Path(reference).read_bytes()
    except OSError:return ()
    try:return _json_preview(raw)
    except (UnicodeError,ValueError,TypeError,AttributeError):return _binary_preview(raw)
