"""Read-only decoder for UNO Synth Pro hardware preset SysEx 0x29 sequence pages.

Confirmed from official Editor capture + DFU comparison:
- page 0 payload = 293 bytes (main preset payload; not decoded here)
- pages 1..4 payload = 192 bytes each
- first 182 bytes are 7-bit packed sequence data
- last 10 bytes are page metadata
- packed data recovers raw page bytes 1..159 exactly
- raw page byte 0 (control for Steps 1/17/33/49) is not reconstructed and stays None

No write/store operation is implemented here.
"""
from typing import Dict,List,Optional,Any

RESPONSE_PREFIX=bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x00,0x29])
PAGE_PAYLOAD_SIZE=192
PACKED_SIZE=182
STEP_SIZE=10
STEPS_PER_PAGE=16

def parse_0x29_response(data:bytes,expected_slot=None):
    data=bytes(data)
    if len(data)<12 or not data.startswith(RESPONSE_PREFIX) or data[-1]!=0xF7:return None
    bank=data[8]&0x7F;program=data[9]&0x7F;slot=bank*128+program+1
    if expected_slot is not None and slot!=max(1,min(256,int(expected_slot))):return None
    page=data[10]&0x7F;payload=data[11:-1]
    expected=293 if page==0 else PAGE_PAYLOAD_SIZE if 1<=page<=4 else None
    if expected is None or len(payload)!=expected:return None
    return page,payload

def _unpack_tail(payload:bytes)->bytes:
    if len(payload)!=PAGE_PAYLOAD_SIZE:raise ValueError(f'0x29 sequence page must be 192 bytes, got {len(payload)}')
    bits=[]
    for b in payload[:PACKED_SIZE]:
        v=b&0x7F
        bits.extend((v>>i)&1 for i in range(7))
    bits=bits[:159*8]
    out=bytearray()
    for pos in range(0,len(bits),8):
        v=0
        for i,bit in enumerate(bits[pos:pos+8]):v|=(bit&1)<<i
        out.append(v)
    return bytes(out)

def decode_pages(pages:Dict[int,bytes])->Dict[str,Any]:
    missing=[p for p in range(1,5) if p not in pages]
    if missing:raise ValueError(f'missing 0x29 sequence pages: {missing}')
    steps=[];metadata=[]
    for page in range(1,5):
        payload=bytes(pages[page])
        if len(payload)!=PAGE_PAYLOAD_SIZE:raise ValueError(f'page {page}: expected 192 bytes, got {len(payload)}')
        logical:[Optional[int]]=[None]+list(_unpack_tail(payload))
        metadata.append(payload[PACKED_SIZE:].hex(' '))
        for local in range(STEPS_PER_PAGE):
            rec=logical[local*STEP_SIZE:(local+1)*STEP_SIZE]
            notes=[];vels=[];extras=[]
            for voice in range(3):
                base=1+voice*3;note=rec[base];vel=rec[base+1];extra=rec[base+2]
                if note is None or vel is None or extra is None:raise ValueError('unexpected incomplete note tuple')
                if note!=0xFF and 0<=note<=127:
                    notes.append(note);vels.append(vel&0x7F);extras.append(extra&0xFF)
            steps.append({'step':(page-1)*16+local+1,'control_raw':rec[0],
                          'notes':notes,'note_velocities':vels,'note_extras':extras})
    return {'steps':steps,'metadata':metadata,'unknown_control_steps':[1,17,33,49]}

def apply_to_sequence(sequence,pages:Dict[int,bytes]):
    info=decode_pages(pages);active_last=0
    for item in info['steps']:
        idx=item['step']-1;st=sequence.steps[idx]
        st.notes=list(item['notes']);st.note_velocities=list(item['note_velocities']);st.note_extras=list(item['note_extras'])
        st.control_raw=item['control_raw']
        if st.note_velocities:st.velocity=st.note_velocities[0]
        if st.notes:active_last=idx+1
    sequence.length=max(16,active_last)
    sequence.length_confirmed=False
    sequence.binary_page_headers=[]
    sequence.binary_page_metadata=list(info['metadata'])
    return info
