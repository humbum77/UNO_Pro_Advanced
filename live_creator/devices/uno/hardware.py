"""Read-only UNO Synth Pro hardware preset catalog/sequence reader.

Uses only confirmed 0x24 preset-name reads and 0x29 page reads inherited from
UNO Pro Advanced v0.9.7-beta. No STORE/0x28/write command exists in this module.
"""
from __future__ import annotations
import sys

IK_HEADER=bytes([0xF0,0x00,0x21,0x1A,0x02,0x03])
NAME_PREFIX=IK_HEADER+bytes([0x24,0x01])
PAGE_PREFIX=IK_HEADER+bytes([0x00,0x29])

def preset_name_read(slot):
    n=max(1,min(256,int(slot)))-1
    return NAME_PREFIX+bytes([n//128,n%128,0xF7])

def preset_page_read(slot,page):
    n=max(1,min(256,int(slot)))-1;page=max(0,min(4,int(page)))
    return IK_HEADER+bytes([0x29,n//128,n%128,page,0xF7])

def decode_preset_name_response(data):
    data=bytes(data)
    if len(data)<43 or data[:6]!=IK_HEADER or data[7]!=0x24:return None
    slot=(data[9]&0x7F)*128+(data[10]&0x7F)+1
    if not 1<=slot<=256:return None
    raw=data[11:-1].split(b'\x00',1)[0]
    return slot,raw.decode('ascii','ignore').strip()

def parse_page(data,expected_slot=None):
    data=bytes(data);prefix=IK_HEADER+bytes([0x00,0x29])
    if len(data)<12 or not data.startswith(prefix) or data[-1]!=0xF7:return None
    slot=(data[8]&0x7F)*128+(data[9]&0x7F)+1
    if expected_slot is not None and slot!=int(expected_slot):return None
    page=data[10]&0x7F;payload=data[11:-1]
    if page==0:return (page,payload) if len(payload)==293 else None
    if 1<=page<=4 and len(payload)>=192:return page,payload
    return None

def pages_have_sequence(pages):
    """True/False after full decode; None means incomplete/unsupported."""
    if any(p not in pages for p in range(5)):return None
    try:
        from .unosyp_seq_decoder import decode_payload_note_steps
        for page in range(1,5):
            for step in decode_payload_note_steps(bytes(pages[page]),page-1):
                if any(not voice['empty'] and 0<=voice['note_raw']<=127 for voice in step['voices']):return True
        return False
    except Exception:return None

class HardwareReader:
    def __init__(self,on_event):
        self.on_event=on_event;self.inp=None;self.out=None;self.mod=None;self.connected=False
        self.names={};self.sequence_status={};self.pages={};self.scan_slot=None;self.scan_page=0
    def connect_auto(self):
        if not sys.platform.startswith('win'):return False,'Hardware MIDI reader is available on Windows.'
        try:
            from . import midi_interface as m
            self.mod=m
            ins=m.get_inputs();outs=m.get_outputs()
            def pick(items):
                return next(((i,n) for i,n in items if 'uno synth pro' in n.lower()),None)
            inn=pick(ins);out=pick(outs)
            if not inn or not out:return False,'UNO Synth Pro MIDI ports not found.'
            self.out=m.MidiOut(out[0]);self.inp=m.MidiIn(inn[0],self._rx);self.inp.open();self.connected=True
            return True,f'Connected: {inn[1]}'
        except Exception as e:
            self.close();return False,str(e)
    def _send(self,data):
        if not self.connected or not self.out:return False
        try:self.out.send_sysex(data);return True
        except Exception:return False
    def request_name(self,slot):return self._send(preset_name_read(slot))
    def request_page(self,slot,page):return self._send(preset_page_read(slot,page))
    def _rx(self,data,is_sysex):
        if not is_sysex:return
        decoded=decode_preset_name_response(data)
        if decoded:
            slot,name=decoded;self.names[slot]=name;self.on_event('name',slot,name);return
        parsed=parse_page(data,self.scan_slot)
        if parsed and self.scan_slot is not None:
            page,payload=parsed
            if page!=self.scan_page:return
            self.pages[page]=bytes(payload);self.on_event('page',self.scan_slot,page)
    def close(self):
        for obj in (self.inp,self.out):
            if obj:
                try:obj.close()
                except Exception:pass
        self.inp=self.out=None;self.connected=False
