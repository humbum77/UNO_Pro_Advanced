"""Independent ripple model. All step numbers are computed, one-based."""
from dataclasses import dataclass, replace
from uuid import uuid4

@dataclass(frozen=True)
class PresetBlock:
    id: str
    preset: str | None
    length: int = 1

@dataclass(frozen=True)
class SongStep:
    number: int
    block_id: str
    preset: str | None

class Arrangement:
    maximum = 64
    def __init__(self):
        self.blocks = ()
        self.selected_step = None
        self.playhead = None
        self.selection = set()
        self.loop_range = None
        self.playing = False
        self.tempo = 120
    def set_tempo(self, value):
        value=int(value)
        if not 20<=value<=300:raise ValueError('Tempo must be 20–300 BPM')
        self.tempo=value
    def start(self):
        if not self.length:return
        self.playhead=self.selected_step or 1
        if self.loop_range and not self.loop_range[0]<=self.playhead<=self.loop_range[1]:self.playhead=self.loop_range[0]
        self.playing=True
    def stop(self):self.playing=False
    def advance(self):
        if not self.playing:return
        end=self.loop_range[1] if self.loop_range else self.length
        if self.playhead>=end:
            if self.loop_range:self.playhead=self.loop_range[0]
            else:self.stop()
        else:self.playhead+=1
    def toggle_loop(self):
        spans=[(s,e) for b,s,e in self.ranges() if b.id in self.selection]
        if not spans:return
        value=(min(s for s,e in spans),max(e for s,e in spans))
        self.loop_range=None if self.loop_range==value else value
    def set_playhead(self, number):
        if number is not None and number not in range(1,self.length+1):raise ValueError('Unused Song Step')
        self.playhead=number
    @property
    def length(self):
        return sum(b.length for b in self.blocks)
    def ranges(self):
        start = 1
        for b in self.blocks:
            yield b, start, start+b.length-1
            start += b.length
    def steps(self):
        return tuple(SongStep(n,b.id,b.preset) for b,s,e in self.ranges() for n in range(s,e+1))
    def index(self, id):
        return next(i for i,b in enumerate(self.blocks) if b.id == id)
    def select(self, n, additive=False):
        if n not in range(1,self.length+1): raise ValueError('Unused Song Step')
        self.selected_step = n
        id=self.steps()[n-1].block_id
        if additive:
            if id in self.selection:
                self.selection.remove(id)
                self.selected_step=next((s for b,s,e in self.ranges() if b.id in self.selection),None)
            else:self.selection.add(id)
        else:self.selection={id}
    def commit(self, blocks):
        if any(type(b.length) is not int or b.length < 1 for b in blocks):
            raise ValueError('Length must be a positive integer')
        if sum(b.length for b in blocks)>64: raise ValueError('64-step limit reached')
        old=next(((b.id,self.selected_step-s) for b,s,e in self.ranges()
                  if self.selected_step is not None and s<=self.selected_step<=e),None)
        self.blocks=tuple(blocks)
        self.selection.intersection_update(b.id for b in blocks)
        self.loop_range=None
        self.playing=False
        if self.playhead is not None and self.playhead>self.length:self.playhead=None
        if old:
            self.selected_step=next((s+min(old[1],b.length-1) for b,s,e in self.ranges() if b.id==old[0]),min(self.selected_step,self.length) or None)
    def insert(self,index,preset,length=1):
        if not 0<=index<=len(self.blocks): raise ValueError('Invalid position')
        b=PresetBlock(uuid4().hex,preset,length); items=list(self.blocks); items.insert(index,b)
        self.commit(items); return b.id
    def replace(self,id,preset):
        items=list(self.blocks); i=self.index(id); items[i]=replace(items[i],preset=preset); self.commit(items)
    def delete_selected(self):
        if not self.selection:return
        self.commit([b for b in self.blocks if b.id not in self.selection])
        self.selection.clear();self.selected_step=None
    def insert_at_slot(self,index,preset,slot):
        items=list(self.blocks)
        if index==len(items) and slot>self.length+1:
            items.append(PresetBlock(uuid4().hex,None,slot-self.length-1));index=len(items)
        items.insert(index,PresetBlock(uuid4().hex,preset,1));self.commit(items)
    def resize(self,id,length):
        items=list(self.blocks); i=self.index(id); items[i]=replace(items[i],length=length); self.commit(items)
    def move(self,id,delta):
        if type(delta) is not int: raise ValueError('Whole steps required')
        if not delta: return
        items=list(self.blocks); i=self.index(id)
        if items[i].preset is None: raise ValueError('Move a preset to edit the gap')
        gap=i>0 and items[i-1].preset is None
        if delta>0:
            if gap: items[i-1]=replace(items[i-1],length=items[i-1].length+delta)
            else: items.insert(i,PresetBlock(uuid4().hex,None,delta))
        else:
            if not gap or items[i-1].length < -delta: raise ValueError('Cannot cross preceding block')
            size=items[i-1].length+delta
            if size: items[i-1]=replace(items[i-1],length=size)
            else: items.pop(i-1)
        self.commit(items)
