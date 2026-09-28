import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
from pathlib import Path

APP_TITLE = "UNO Synth Pro MIDI Monitor v1.1 State Read"
STATE_REQUEST = bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x37,0x00,0x00,0xF7])

winmm = ctypes.WinDLL("winmm.dll")
UINT = ctypes.c_uint
DWORD_PTR = ctypes.c_void_p
CALLBACK_FUNCTION = 0x00030000
MIM_DATA = 0x3C3
MIM_LONGDATA = 0x3C4
MHDR_DONE = 0x00000001
MAXPNAMELEN = 32

class MIDIINCAPS(ctypes.Structure):
    _fields_=[("wMid",wintypes.WORD),("wPid",wintypes.WORD),("vDriverVersion",wintypes.UINT),("szPname",wintypes.WCHAR*MAXPNAMELEN),("dwSupport",wintypes.DWORD)]
class MIDIOUTCAPS(ctypes.Structure):
    _fields_=[("wMid",wintypes.WORD),("wPid",wintypes.WORD),("vDriverVersion",wintypes.UINT),("szPname",wintypes.WCHAR*MAXPNAMELEN),("wTechnology",wintypes.WORD),("wVoices",wintypes.WORD),("wNotes",wintypes.WORD),("wChannelMask",wintypes.WORD),("dwSupport",wintypes.DWORD)]
class MIDIHDR(ctypes.Structure):
    _fields_=[("lpData",ctypes.POINTER(ctypes.c_char)),("dwBufferLength",wintypes.DWORD),("dwBytesRecorded",wintypes.DWORD),("dwUser",DWORD_PTR),("dwFlags",wintypes.DWORD),("lpNext",ctypes.c_void_p),("reserved",DWORD_PTR),("dwOffset",wintypes.DWORD),("dwReserved",wintypes.DWORD*8)]
CALLBACK=ctypes.WINFUNCTYPE(None,wintypes.HANDLE,wintypes.UINT,DWORD_PTR,DWORD_PTR,DWORD_PTR)

winmm.midiInGetNumDevs.restype=UINT
winmm.midiInGetDevCapsW.argtypes=[UINT,ctypes.POINTER(MIDIINCAPS),UINT]
winmm.midiInOpen.argtypes=[ctypes.POINTER(wintypes.HANDLE),UINT,DWORD_PTR,DWORD_PTR,wintypes.DWORD]
winmm.midiInStart.argtypes=[wintypes.HANDLE]
winmm.midiInStop.argtypes=[wintypes.HANDLE]
winmm.midiInReset.argtypes=[wintypes.HANDLE]
winmm.midiInClose.argtypes=[wintypes.HANDLE]
winmm.midiInPrepareHeader.argtypes=[wintypes.HANDLE,ctypes.POINTER(MIDIHDR),UINT]
winmm.midiInUnprepareHeader.argtypes=[wintypes.HANDLE,ctypes.POINTER(MIDIHDR),UINT]
winmm.midiInAddBuffer.argtypes=[wintypes.HANDLE,ctypes.POINTER(MIDIHDR),UINT]
winmm.midiOutGetNumDevs.restype=UINT
winmm.midiOutGetDevCapsW.argtypes=[UINT,ctypes.POINTER(MIDIOUTCAPS),UINT]
winmm.midiOutOpen.argtypes=[ctypes.POINTER(wintypes.HANDLE),UINT,DWORD_PTR,DWORD_PTR,wintypes.DWORD]
winmm.midiOutShortMsg.argtypes=[wintypes.HANDLE,wintypes.DWORD]
winmm.midiOutPrepareHeader.argtypes=[wintypes.HANDLE,ctypes.POINTER(MIDIHDR),UINT]
winmm.midiOutLongMsg.argtypes=[wintypes.HANDLE,ctypes.POINTER(MIDIHDR),UINT]
winmm.midiOutUnprepareHeader.argtypes=[wintypes.HANDLE,ctypes.POINTER(MIDIHDR),UINT]
winmm.midiOutClose.argtypes=[wintypes.HANDLE]

def input_devices():
    out=[]
    for i in range(winmm.midiInGetNumDevs()):
        c=MIDIINCAPS()
        if winmm.midiInGetDevCapsW(i,ctypes.byref(c),ctypes.sizeof(c))==0: out.append((i,c.szPname))
    return out

def output_devices():
    out=[]
    for i in range(winmm.midiOutGetNumDevs()):
        c=MIDIOUTCAPS()
        if winmm.midiOutGetDevCapsW(i,ctypes.byref(c),ctypes.sizeof(c))==0: out.append((i,c.szPname))
    return out

class MidiIn:
    def __init__(self,dev_id,cb,buffer_size=16384,buffers=16):
        self.dev_id=dev_id; self.cb_py=cb; self.handle=wintypes.HANDLE(); self.cb=CALLBACK(self._callback); self.running=False; self.bufs=[]; self.buffer_size=buffer_size; self.buffer_count=buffers
    def open(self):
        r=winmm.midiInOpen(ctypes.byref(self.handle),self.dev_id,ctypes.cast(self.cb,DWORD_PTR),0,CALLBACK_FUNCTION)
        if r: raise RuntimeError(f"midiInOpen error {r}")
        for _ in range(self.buffer_count):
            buf=ctypes.create_string_buffer(self.buffer_size); hdr=MIDIHDR(); hdr.lpData=ctypes.cast(buf,ctypes.POINTER(ctypes.c_char)); hdr.dwBufferLength=self.buffer_size
            self.bufs.append((buf,hdr))
            r=winmm.midiInPrepareHeader(self.handle,ctypes.byref(hdr),ctypes.sizeof(hdr))
            if r: raise RuntimeError(f"midiInPrepareHeader error {r}")
            r=winmm.midiInAddBuffer(self.handle,ctypes.byref(hdr),ctypes.sizeof(hdr))
            if r: raise RuntimeError(f"midiInAddBuffer error {r}")
        self.running=True
        r=winmm.midiInStart(self.handle)
        if r: raise RuntimeError(f"midiInStart error {r}")
    def _callback(self,h,wmsg,inst,p1,p2):
        if not self.running: return
        try:
            if wmsg==MIM_DATA:
                packed=int(p1); status=packed&0xFF
                if status>=0xF8: data=bytes([status])
                elif (status&0xF0) in (0xC0,0xD0): data=bytes([status,(packed>>8)&0xFF])
                else: data=bytes([status,(packed>>8)&0xFF,(packed>>16)&0xFF])
                self.cb_py(data,False)
            elif wmsg==MIM_LONGDATA:
                hp=ctypes.cast(p1,ctypes.POINTER(MIDIHDR)); hdr=hp.contents
                if hdr.dwBytesRecorded: self.cb_py(ctypes.string_at(hdr.lpData,hdr.dwBytesRecorded),True)
                if self.running: winmm.midiInAddBuffer(self.handle,hp,ctypes.sizeof(hdr))
        except Exception as e: print("MIDI callback error:",e)
    def close(self):
        self.running=False
        if not self.handle: return
        try: winmm.midiInStop(self.handle)
        except: pass
        try: winmm.midiInReset(self.handle)
        except: pass
        time.sleep(0.02)
        for _,hdr in self.bufs:
            try: winmm.midiInUnprepareHeader(self.handle,ctypes.byref(hdr),ctypes.sizeof(hdr))
            except: pass
        try: winmm.midiInClose(self.handle)
        except: pass
        self.handle=None

class MidiOut:
    def __init__(self,dev_id):
        self.handle=wintypes.HANDLE(); r=winmm.midiOutOpen(ctypes.byref(self.handle),dev_id,0,0,0)
        if r: raise RuntimeError(f"midiOutOpen error {r}")
        self.lock=threading.Lock()
    def send(self,data):
        data=bytes(data)
        with self.lock:
            if data and data[0]==0xF0:
                buf=ctypes.create_string_buffer(data); hdr=MIDIHDR(); hdr.lpData=ctypes.cast(buf,ctypes.POINTER(ctypes.c_char)); hdr.dwBufferLength=len(data)
                r=winmm.midiOutPrepareHeader(self.handle,ctypes.byref(hdr),ctypes.sizeof(hdr))
                if r: raise RuntimeError(f"midiOutPrepareHeader error {r}")
                r=winmm.midiOutLongMsg(self.handle,ctypes.byref(hdr),ctypes.sizeof(hdr))
                if r: raise RuntimeError(f"midiOutLongMsg error {r}")
                for _ in range(1000):
                    if hdr.dwFlags & MHDR_DONE: break
                    time.sleep(0.001)
                winmm.midiOutUnprepareHeader(self.handle,ctypes.byref(hdr),ctypes.sizeof(hdr))
            else:
                packed=int.from_bytes(data.ljust(3,b'\0'),'little'); r=winmm.midiOutShortMsg(self.handle,packed)
                if r: raise RuntimeError(f"midiOutShortMsg error {r}")
    def close(self):
        if self.handle:
            try: winmm.midiOutClose(self.handle)
            except: pass
            self.handle=None

def decode(data):
    if not data:return ""
    if data[0]==0xF0:
        if len(data)==309 and data[:10]==bytes([0xF0,0,0x21,0x1A,2,3,0,0x37,0,0]): return "UNO state 309B"
        return f"SysEx ({len(data)} bytes)"
    s=data[0]
    if s==0xF8:return "Clock"
    if s==0xFE:return "Active Sense"
    st=s&0xF0; ch=(s&0x0F)+1
    names={0x80:"Note Off",0x90:"Note On",0xA0:"Poly AT",0xB0:"CC",0xC0:"Program",0xD0:"Channel AT",0xE0:"Pitch Bend"}
    return f"{names.get(st,'MIDI')} ch {ch} " + " ".join(f"{x:02X}" for x in data[1:])

class App:
    def __init__(self,root):
        self.root=root; root.title(APP_TITLE); root.geometry("1450x850")
        self.ins=[]; self.outs=[]; self.uno_in=None; self.tap_in=None; self.uno_out=None; self.return_out=None; self.start_time=None; self.records=[]; self.running=False
        self.capture_clock=tk.BooleanVar(value=False); self.capture_active=tk.BooleanVar(value=False)
        self._build(); self.refresh(); root.protocol("WM_DELETE_WINDOW",self.close)
    def _build(self):
        top=ttk.Frame(self.root,padding=8); top.pack(fill="x")
        labels=["UNO IN","UNO OUT","EDITOR OUT / TAP IN","EDITOR IN / RETURN OUT"]
        self.cbs=[]
        for r,lbl in enumerate(labels):
            ttk.Label(top,text=lbl).grid(row=r,column=0,sticky="w",pady=2)
            cb=ttk.Combobox(top,state="readonly",width=55); cb.grid(row=r,column=1,sticky="ew",padx=8,pady=2); self.cbs.append(cb)
        top.columnconfigure(1,weight=1)
        b=ttk.Frame(top); b.grid(row=0,column=2,rowspan=4,padx=5)
        ttk.Button(b,text="Refresh",command=self.refresh).pack(fill="x",pady=2)
        self.start_btn=ttk.Button(b,text="START",command=self.toggle); self.start_btn.pack(fill="x",pady=2)
        self.read_btn=ttk.Button(b,text="READ STATE 0x37",command=self.read_state,state="disabled"); self.read_btn.pack(fill="x",pady=2)
        ttk.Button(b,text="Clear",command=self.clear).pack(fill="x",pady=2)
        ttk.Button(b,text="Save",command=self.save).pack(fill="x",pady=2)
        opts=ttk.Frame(self.root,padding=(8,0,8,6)); opts.pack(fill="x")
        ttk.Checkbutton(opts,text="Capture MIDI Clock",variable=self.capture_clock).pack(side="left")
        ttk.Checkbutton(opts,text="Capture Active Sense",variable=self.capture_active).pack(side="left",padx=12)
        self.status=ttk.Label(opts,text="Ready"); self.status.pack(side="right")
        f=ttk.Frame(self.root,padding=(8,0,8,8)); f.pack(fill="both",expand=True)
        cols=("n","time","direction","type","bytes","hex","decoded")
        self.tree=ttk.Treeview(f,columns=cols,show="headings")
        widths=(60,100,120,80,70,720,260)
        for c,w in zip(cols,widths): self.tree.heading(c,text=c.upper()); self.tree.column(c,width=w,anchor="w")
        self.tree.pack(side="left",fill="both",expand=True)
        sy=ttk.Scrollbar(f,orient="vertical",command=self.tree.yview); sy.pack(side="right",fill="y"); self.tree.configure(yscrollcommand=sy.set)
        self.detail=tk.Text(self.root,height=6,wrap="none"); self.detail.pack(fill="x",padx=8,pady=(0,8)); self.tree.bind("<<TreeviewSelect>>",self.select)
        ttk.Label(self.root,text="READ STATE sends only the confirmed non-destructive request: F0 00 21 1A 02 03 37 00 00 F7",padding=(8,0,8,8)).pack(fill="x")
    def _find_index(self,items,terms):
        for k,(_,name) in enumerate(items):
            n=name.lower()
            if any(t.lower() in n for t in terms): return k
        return 0 if items else -1
    def refresh(self):
        self.ins=input_devices(); self.outs=output_devices(); iv=[f"{i}: {n}" for i,n in self.ins]; ov=[f"{i}: {n}" for i,n in self.outs]
        self.cbs[0]["values"]=iv; self.cbs[1]["values"]=ov; self.cbs[2]["values"]=iv; self.cbs[3]["values"]=ov
        if iv:
            self.cbs[0].current(self._find_index(self.ins,["UNO Synth Pro"])); self.cbs[2].current(self._find_index(self.ins,["UNO_TAP"]))
        if ov:
            self.cbs[1].current(self._find_index(self.outs,["UNO Synth Pro"])); self.cbs[3].current(self._find_index(self.outs,["UNO_RETURN"]))
        self.status.config(text=f"{len(iv)} inputs / {len(ov)} outputs")
    def toggle(self):
        self.stop() if self.running else self.start()
    def start(self):
        try:
            ii0=self.cbs[0].current(); oo0=self.cbs[1].current(); ii1=self.cbs[2].current(); oo1=self.cbs[3].current()
            if min(ii0,oo0,ii1,oo1)<0: raise RuntimeError("Select all four MIDI ports")
            self.uno_out=MidiOut(self.outs[oo0][0]); self.return_out=MidiOut(self.outs[oo1][0])
            self.uno_in=MidiIn(self.ins[ii0][0],lambda d,l:self.received("UNO→EDITOR",d,l)); self.tap_in=MidiIn(self.ins[ii1][0],lambda d,l:self.received("EDITOR→UNO",d,l))
            self.uno_in.open(); self.tap_in.open(); self.start_time=time.perf_counter(); self.running=True
            self.start_btn.config(text="STOP"); self.read_btn.config(state="normal"); self.status.config(text="Proxy running")
        except Exception as e:
            self._close_ports(); messagebox.showerror("MIDI",str(e))
    def stop(self):
        self.running=False; self.read_btn.config(state="disabled"); self.start_btn.config(text="START"); self.status.config(text="Stopped"); self._close_ports()
    def _close_ports(self):
        for a in ("uno_in","tap_in","uno_out","return_out"):
            obj=getattr(self,a,None)
            if obj:
                try: obj.close()
                except: pass
                setattr(self,a,None)
    def received(self,direction,data,is_long):
        if not self.running:return
        # Proxy first, log second. Never alter the user's MIDI stream.
        try:
            if direction=="UNO→EDITOR" and self.return_out:self.return_out.send(data)
            elif direction=="EDITOR→UNO" and self.uno_out:self.uno_out.send(data)
        except Exception as e:self.root.after(0,lambda:self.status.config(text=f"Forward error: {e}"))
        if data==b'\xF8' and not self.capture_clock.get():return
        if data==b'\xFE' and not self.capture_active.get():return
        self.log(direction,data,is_long)
    def log(self,direction,data,is_long=False):
        elapsed=(time.perf_counter()-self.start_time) if self.start_time else 0.0; typ="SysEx" if (is_long or (data and data[0]==0xF0)) else "MIDI"; hx=" ".join(f"{x:02X}" for x in data); rec=(elapsed,direction,typ,len(data),hx,decode(data)); self.records.append(rec); self.root.after(0,self._add,rec)
    def _add(self,r):
        e,d,t,n,hx,dec=r; self.tree.insert("","end",values=(len(self.records),f"{e:.6f}",d,t,n,hx,dec)); self.tree.yview_moveto(1)
    def read_state(self):
        if not self.running or not self.uno_out: messagebox.showwarning("READ STATE","Start the monitor first."); return
        try:
            self.uno_out.send(STATE_REQUEST); self.log("MONITOR→UNO",STATE_REQUEST,True); self.status.config(text="0x37 state request sent — waiting for 309B response")
        except Exception as e: messagebox.showerror("READ STATE",str(e))
    def clear(self):
        for x in self.tree.get_children():self.tree.delete(x)
        self.records.clear(); self.detail.delete("1.0","end")
    def select(self,_=None):
        s=self.tree.selection()
        if not s:return
        v=self.tree.item(s[0])["values"]; self.detail.delete("1.0","end"); self.detail.insert("1.0",f"REC {v[0]} | {v[1]} s | {v[2]} | {v[3]} | {v[4]} bytes\n{v[5]}\n{v[6]}")
    def save(self):
        if not self.records: messagebox.showinfo("Save","No data"); return
        stamp=time.strftime("%Y%m%d_%H%M%S"); p=filedialog.asksaveasfilename(initialfile=f"uno_monitor_capture_{stamp}.txt",defaultextension=".txt",filetypes=[("Text","*.txt")])
        if not p:return
        with open(p,"w",encoding="utf-8") as f:
            f.write(APP_TITLE+"\n"); f.write(f"UNO IN: {self.cbs[0].get()}\nUNO OUT: {self.cbs[1].get()}\nEDITOR OUT/TAP IN: {self.cbs[2].get()}\nEDITOR IN/RETURN OUT: {self.cbs[3].get()}\n"); f.write(f"Clock captured: {self.capture_clock.get()}\nActive Sense captured: {self.capture_active.get()}\n"); f.write("REC\tTIME\tDIRECTION\tTYPE\tBYTES\tHEX\tDECODED\n")
            for i,r in enumerate(self.records,1): f.write(f"{i}\t{r[0]:.6f}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\t{r[5]}\n")
        messagebox.showinfo("Saved",p)
    def close(self):
        self.stop(); self.root.destroy()

if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()
