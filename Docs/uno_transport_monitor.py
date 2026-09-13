"""Standalone MIDI transport/MMC monitor for UNO experiments.

This tool is deliberately read/transport-only: it never reads presets, sends
0x29/0x37/0x24 requests, or guesses SEQ ON/OFF commands.
"""
from __future__ import annotations
import sys,time,queue,tkinter as tk
from pathlib import Path
from tkinter import ttk,filedialog,messagebox
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from midi_engine import MidiEngine

def describe(data,sysex):
    b=bytes(data); hx=' '.join(f'{x:02X}' for x in b)
    if not sysex and len(b)==1:return {0xF8:'Timing Clock',0xFA:'Start',0xFB:'Continue',0xFC:'Stop',0xFE:'Active Sensing',0xFF:'System Reset'}.get(b[0],'Realtime')
    if sysex and len(b)>=6 and b[:3]==b'\xF0\x7F\x7F' and b[3:5]==b'\x06\x01': return 'MMC Stop' if b[5:6]==b'\x01' else 'MMC Play' if b[5:6]==b'\x02' else f'MMC command {b[5]:02X}'
    if not sysex and b and (b[0]&0xF0)==0xB0:return f'CC {b[1]} = {b[2]}'
    return 'SysEx' if sysex else 'MIDI'

class Monitor(tk.Tk):
 def __init__(self):
  super().__init__();self.title('UNO Transport Monitor');self.geometry('980x620');self.q=queue.Queue();self.m=MidiEngine(self._rx);self.ins=[];self.outs=[];self.invar=tk.StringVar();self.outvar=tk.StringVar();self._build();self.refresh();self.after(30,self._drain)
 def _build(self):
  top=ttk.Frame(self);top.pack(fill='x',padx=8,pady=8)
  ttk.Label(top,text='MIDI IN').pack(side='left');self.inbox=ttk.Combobox(top,textvariable=self.invar,width=28,state='readonly');self.inbox.pack(side='left',padx=5)
  ttk.Label(top,text='MIDI OUT').pack(side='left',padx=(16,0));self.outbox=ttk.Combobox(top,textvariable=self.outvar,width=28,state='readonly');self.outbox.pack(side='left',padx=5)
  ttk.Button(top,text='Refresh',command=self.refresh).pack(side='left',padx=5);ttk.Button(top,text='Connect',command=self.connect).pack(side='left')
  bar=ttk.Frame(self);bar.pack(fill='x',padx=8)
  for label,fn in [('PLAY',self.play),('STOP',self.stop),('CONTINUE',self.cont),('MMC PLAY',lambda:self.mm(2)),('MMC STOP',lambda:self.mm(1)),('Clear',self.clear),('Save capture',self.save)]:ttk.Button(bar,text=label,command=fn).pack(side='left',padx=3)
  self.text=tk.Text(self,height=28,bg='#11171a',fg='#e8edf0',insertbackground='white');self.text.pack(fill='both',expand=True,padx=8,pady=8)
 def refresh(self):
  try:self.ins=self.m.inputs();self.outs=self.m.outputs()
  except Exception as e:self.ins=[];self.outs=[];self.log('ERROR',str(e))
  self.inbox['values']=self.ins;self.outbox['values']=self.outs
  if self.ins and not self.invar.get():self.invar.set(self.ins[0])
  if self.outs and not self.outvar.get():self.outvar.set(self.outs[0])
 def connect(self):
  ok,msg=self.m.connect(self.invar.get(),self.outvar.get(),1,1,'Off');self.log('INFO',msg)
 def _rx(self,data,sysex):self.q.put((time.time(),'IN',bytes(data),sysex))
 def log(self,direction,msg,data=b'',sysex=False):
  stamp=time.strftime('%H:%M:%S')+'.%03d'%int((time.time()%1)*1000); self.text.insert('end',f'{stamp} {direction:>5} {describe(data,sysex):<20} {" ".join(f"{x:02X}" for x in data)} {msg}\n');self.text.see('end')
 def _drain(self):
  while True:
   try:
    t,d,b,s=self.q.get_nowait();self.log(d,'',b,s)
   except queue.Empty:break
  self.after(30,self._drain)
 def _send(self,data,sysex=False):
  ok=self.m.sysex(data) if sysex else self.m._short(data[0]);self.log('OUT','sent' if ok else 'not connected',data,sysex)
 def play(self):self._send(b'\xFA')
 def stop(self):self._send(b'\xFC')
 def cont(self):self._send(b'\xFB')
 def mm(self,cmd):self._send(bytes([0xF0,0x7F,0x7F,0x06,cmd,0xF7]),True)
 def clear(self):self.text.delete('1.0','end')
 def save(self):
  p=filedialog.asksaveasfilename(defaultextension='.txt',filetypes=[('Text','*.txt')]);
  if p:Path(p).write_text(self.text.get('1.0','end'),encoding='utf-8')
 def destroy(self):self.m.close();super().destroy()

if __name__=='__main__':Monitor().mainloop()
