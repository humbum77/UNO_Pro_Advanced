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
from typing import Dict,Any
from unosyp_seq_decoder import decode_gate_accent_values,decode_payload_note_steps,parse_payload_page
from uno_step_automation_decoder import decode_page_payloads
from native_automation import apply_decoded_to_sequence

RESPONSE_PREFIX=bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x00,0x29])
PAGE_PAYLOAD_SIZE=192
MAX_PAGE_PAYLOAD_SIZE=65535
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
    # Sequence pages may carry an extension after the confirmed 192-byte core.
    if expected is None or (page==0 and len(payload)!=expected) or (1<=page<=4 and not (expected<=len(payload)<=MAX_PAGE_PAYLOAD_SIZE)):return None
    return page,payload

def decode_pages(pages:Dict[int,bytes])->Dict[str,Any]:
    missing=[p for p in range(0,5) if p not in pages]
    if missing:raise ValueError(f'missing 0x29 sequence pages: {missing}')
    gate_value,accent_value=decode_gate_accent_values(page0_payload=pages[0])
    steps=[];metadata=[];decoded_pages=[]
    for page in range(1,5):
        payload=bytes(pages[page])
        if len(payload)<PAGE_PAYLOAD_SIZE:raise ValueError(f'page {page}: expected at least 192 bytes, got {len(payload)}')
        decoded=parse_payload_page(payload,page-1,gate_value,accent_value)
        note_steps=decode_payload_note_steps(payload,page-1)
        decoded_pages.append(decoded);metadata.append(decoded['metadata_hex'])
        for note_item,automation_item in zip(note_steps,decoded['steps']):
            notes=[];vels=[];extras=[]
            for voice in note_item['voices']:
                if voice['empty']:continue
                note=voice['note_raw']
                if 0<=note<=127:
                    notes.append(note);vels.append(voice['velocity']&0x7F);extras.append(voice['extra_raw']&0xFF)
            steps.append({'step':note_item['step'],'control_raw':note_item['control_raw'],
                          'notes':notes,'note_velocities':vels,'note_extras':extras,
                          'gate':automation_item['gate'],'accent':automation_item['accent'],
                          'tie':automation_item['tie']})
    automation=decode_page_payloads([pages[page] for page in range(1,5)])
    return {'steps':steps,'metadata':metadata,'pages':decoded_pages,
            'gate_value':gate_value,'accent_value':accent_value,
            'automation':automation}

def apply_to_sequence(sequence,pages:Dict[int,bytes]):
    info=decode_pages(pages);active_last=0
    for item in info['steps']:
        idx=item['step']-1;st=sequence.steps[idx]
        st.notes=list(item['notes']);st.note_velocities=list(item['note_velocities']);st.note_extras=list(item['note_extras'])
        st.control_raw=item['control_raw']
        st.gate=max(0,min(10,int(item.get('gate',0))))
        st.accent=max(0,min(127,int(item.get('accent',0))))
        st.tie=bool(item.get('tie',False))
        if st.note_velocities:st.velocity=st.note_velocities[0]
        if st.notes:active_last=idx+1
    sequence.length=max(16,active_last)
    sequence.length_confirmed=False
    sequence.binary_page_headers=[]
    sequence.binary_page_metadata=list(info['metadata'])
    sequence.binary_page_payloads=[bytes(pages[p]).hex() for p in range(1,5)]
    apply_decoded_to_sequence(sequence,info['automation'])
    return info
