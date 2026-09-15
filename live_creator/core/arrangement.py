"""Independent ripple model. All step numbers are computed, one-based."""
from dataclasses import dataclass, replace, field
from uuid import uuid4

@dataclass(frozen=True)
class PresetBlock:
    id: str
    preset: str | None
    length: int = 1
    color: str | None = None
    parameters: dict = field(default_factory=dict)

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
        self.markers = {}
    def set_marker(self,step,text):
        if step not in [s for b,s,e in self.ranges()]:raise ValueError('Marker must start at a block boundary')
        text=text.strip()[:80]
        if text:self.markers[step]=text
        else:self.markers.pop(step,None)
    def sections(self):
        positions=sorted(self.markers)
        return [(s,positions[i+1]-1 if i+1<len(positions) else self.length,self.markers[s]) for i,s in enumerate(positions)]
    def set_color(self,ids,color):
        self.blocks=tuple(replace(b,color=color) if b.id in ids else b for b in self.blocks)
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
        blocks=tuple(blocks)
        if any(type(b.length) is not int or b.length < 1 for b in blocks):
            raise ValueError('Length must be a positive integer')
        if sum(b.length for b in blocks)>64: raise ValueError('64-step limit reached')
        old=next(((b.id,self.selected_step-s) for b,s,e in self.ranges()
                  if self.selected_step is not None and s<=self.selected_step<=e),None)
        old_ranges=list(self.ranges());new_starts={};position=1
        for b in blocks:new_starts[b.id]=position;position+=b.length
        markers={}
        for step,text in sorted(self.markers.items()):
            following=[b.id for b,s,e in old_ranges if s>=step and b.id in new_starts]
            if following:
                position=new_starts[following[0]]
                previous=markers.get(position)
                if previous is not None and previous!=text:
                    raise ValueError(f'Marker conflict at {position:02d}: operation cancelled; resolve markers first')
                markers[position]=text
        self.markers=markers
        self.blocks=blocks
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
    def resize_left(self,id,delta):
        if type(delta)is not int:raise ValueError('Whole steps required')
        if not delta:return
        items=list(self.blocks);i=self.index(id);block=items[i]
        if block.length-delta<1:raise ValueError('Length must be a positive integer')
        gap=i>0 and items[i-1].preset is None
        if delta<0 and (not gap or items[i-1].length < -delta):raise ValueError('Cannot cross preceding block')
        items[i]=replace(block,length=block.length-delta)
        if gap:
            size=items[i-1].length+delta
            if size:items[i-1]=replace(items[i-1],length=size)
            else:items.pop(i-1)
        elif delta>0:items.insert(i,PresetBlock(uuid4().hex,None,delta))
        self.commit(items)
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
