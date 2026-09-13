import sys,logging
from protocol_map import STATE_READ,preset_name_read,preset_page_read
logger=logging.getLogger(__name__)
class MidiEngine:
 def __init__(self,on_message=None):
  self.on_message=on_message;self.inp=None;self.controller_inp=None;self.out=None;self.input_name='';self.controller_name='';self.output_name='';self.in_channel=0;self.omni=False;self.out_channel=0;self._mod=None;self.available=sys.platform.startswith('win')
  if self.available:
   try:import midi_interface as m;self._mod=m
   except Exception as e:self.available=False;logger.warning('MIDI backend unavailable: %s',e)
 def inputs(self):return [n for _,n in self._mod.get_inputs()] if self.available else []
 def outputs(self):return [n for _,n in self._mod.get_outputs()] if self.available else []
 def connect(self,inn,outn,in_channel=1,out_channel=1,controller='Off'):
  self.close();self.omni=str(in_channel).upper()=='OMNI';self.in_channel=0 if self.omni else max(0,min(15,int(in_channel)-1));self.out_channel=max(0,min(15,int(out_channel)-1))
  if not self.available:return False,'WinMM MIDI works on Windows; offline mode active here.'
  try:
   if outn:
    oid=next(i for i,n in self._mod.get_outputs() if n==outn);self.out=self._mod.MidiOut(oid);self.output_name=outn
   if inn:
    iid=next(i for i,n in self._mod.get_inputs() if n==inn);self.inp=self._mod.MidiIn(iid,self._rx);self.inp.open();self.input_name=inn
   if controller and controller!='Off' and controller!=inn:
    cid=next(i for i,n in self._mod.get_inputs() if n==controller);self.controller_inp=self._mod.MidiIn(cid,self._rx);self.controller_inp.open();self.controller_name=controller
   return True,'Connected'
  except Exception as e:self.close();return False,str(e)
 def _rx(self,data,is_sysex):
  if self.on_message:
   try:self.on_message(bytes(data),is_sysex)
   except Exception:logger.exception('Unhandled exception in MIDI receive callback')
 def _short(self,status,d1=0,d2=0):
  if not self.out:return False
  try:
   packed=(status&255)|((d1&127)<<8)|((d2&127)<<16);self._mod.winmm.midiOutShortMsg(self.out.handle,packed);return True
  except Exception:logger.exception('Failed to send short MIDI message');return False
 def send_cc(self,cc,v):return self._short(0xB0+self.out_channel,int(cc),int(v))
 def program_change(self,p):return self._short(0xC0+self.out_channel,int(p),0)
 def bank_program(self,n):
  n=max(1,min(256,int(n)))-1;return self.send_cc(0,n//128) and self.program_change(n%128)
 def pitch_bend(self,value):
  v=max(0,min(16383,int(value)+8192));return self._short(0xE0+self.out_channel,v&127,(v>>7)&127)
 def note_on(self,n,v=100):return self._short(0x90+self.out_channel,n,v)
 def note_off(self,n):return self._short(0x80+self.out_channel,n,0)
 def sysex(self,d):
  if not self.out:return False
  try:self.out.send_sysex(d);return True
  except Exception:logger.exception('Failed to send SysEx');return False
 def read_state(self):return self.sysex(STATE_READ)
 def read_preset_name(self,n):return self.sysex(preset_name_read(n))
 def read_preset_page(self,slot,page):return self.sysex(preset_page_read(slot,page))
 def clock(self):return self._short(0xF8)
 def start(self):return self._short(0xFA)
 def stop(self):return self._short(0xFC)
 def close(self):
  for a in ('inp','controller_inp','out'):
   o=getattr(self,a,None)
   if o:
    try:o.close()
    except Exception:logger.exception('Failed to close MIDI endpoint %s',a)
   setattr(self,a,None)
