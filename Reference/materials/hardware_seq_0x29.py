"""UNO Synth Pro hardware sequencer read decoder for SysEx command 0x29.

Read-only. No STORE/0x28 and no bootloader operations.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any

IK_HEADER = bytes([0xF0,0x00,0x21,0x1A,0x02,0x03])
RESPONSE_PREFIX = bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x00,0x29,0x00,0x00])
PAGE_PAYLOAD_SIZE=192;PACKED_SIZE=182;META_SIZE=10;RAW_PAGE_SIZE=160;STEP_SIZE=10;STEPS_PER_PAGE=16

def parse_0x29_response(data: bytes):
    data=bytes(data)
    if len(data)<12 or not data.startswith(RESPONSE_PREFIX) or data[-1]!=0xF7:return None
    page=data[10]&0x7F;payload=data[11:-1]
    expected=293 if page==0 else PAGE_PAYLOAD_SIZE if 1<=page<=4 else None
    if expected is None or len(payload)!=expected:return None
    return page,payload

def _bits_lsb7(data:bytes)->List[int]:
    out=[]
    for b in data:
        v=b&0x7F
        for bit in range(7):out.append((v>>bit)&1)
    return out

def _bits_to_bytes_lsb(bits:List[int])->bytes:
    if len(bits)%8:raise ValueError("bit count must be divisible by 8")
    out=bytearray()
    for i in range(0,len(bits),8):
        v=0
        for bit,x in enumerate(bits[i:i+8]):v|=(x&1)<<bit
        out.append(v)
    return bytes(out)

def unpack_page_tail(payload:bytes)->bytes:
    if len(payload)!=PAGE_PAYLOAD_SIZE:raise ValueError(f"0x29 page payload must be 192 bytes, got {len(payload)}")
    bits=_bits_lsb7(payload[:PACKED_SIZE])
    return _bits_to_bytes_lsb(bits[:159*8])

def page_metadata(payload:bytes)->bytes:
    if len(payload)!=PAGE_PAYLOAD_SIZE:raise ValueError(f"0x29 page payload must be 192 bytes, got {len(payload)}")
    return payload[PACKED_SIZE:]

def decode_pages(pages:Dict[int,bytes])->Dict[str,Any]:
    missing=[p for p in range(1,5) if p not in pages]
    if missing:raise ValueError(f"missing 0x29 sequence pages: {missing}")
    steps=[];metadata={}
    for page in range(1,5):
        payload=bytes(pages[page])
        if len(payload)!=PAGE_PAYLOAD_SIZE:raise ValueError(f"page {page}: expected 192 bytes, got {len(payload)}")
        tail=unpack_page_tail(payload);logical:[Optional[int]]=[None]+list(tail);metadata[page]=page_metadata(payload)
        for local in range(STEPS_PER_PAGE):
            rec=logical[local*STEP_SIZE:(local+1)*STEP_SIZE];notes=[];velocities=[];extras=[];voices=[]
            for voice in range(3):
                base=1+voice*3;note=rec[base];vel=rec[base+1];extra=rec[base+2]
                assert note is not None and vel is not None and extra is not None
                if note!=0xFF and 0<=note<=127:
                    notes.append(note);velocities.append(vel&0x7F);extras.append(extra&0xFF)
                    voices.append({"voice":voice+1,"note_raw":note,"velocity":vel&0x7F,"extra_raw":extra&0xFF})
            global_step=(page-1)*16+local+1
            steps.append({"step":global_step,"page":page,"local_step":local+1,"control_raw":rec[0],
                          "control_known":rec[0] is not None,"notes":notes,"note_velocities":velocities,
                          "note_extras":extras,"voices":voices,"note_active":bool(notes)})
    return {"steps":steps,"metadata":metadata,"unknown_control_steps":[1,17,33,49]}

def apply_to_sequence(sequence,pages:Dict[int,bytes]):
    decoded=decode_pages(pages)
    for item in decoded["steps"]:
        st=sequence.steps[item["step"]-1]
        st.notes=list(item["notes"])
        if hasattr(st,"note_velocities"):st.note_velocities=list(item["note_velocities"])
        if hasattr(st,"note_extras"):st.note_extras=list(item["note_extras"])
        if hasattr(st,"control_raw"):st.control_raw=item["control_raw"]
        if item["note_velocities"]:st.velocity=item["note_velocities"][0]
    if hasattr(sequence,"length_confirmed"):sequence.length_confirmed=False
    if hasattr(sequence,"binary_page_metadata"):
        sequence.binary_page_metadata=[decoded["metadata"][p].hex(" ") for p in range(1,5)]
    return decoded
