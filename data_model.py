from dataclasses import dataclass,field,asdict
from typing import List,Dict,Optional
import json
import copy
from automation_metadata import empty_lines
@dataclass
class Step:
    notes:List[int]=field(default_factory=list); velocity:int=100; length:float=1.0; gate:int=0; accent:int=0; tie:bool=False; probability:int=100
    note_velocities:List[int]=field(default_factory=list); note_extras:List[int]=field(default_factory=list); control_raw:Optional[int]=None
@dataclass
class Sequence:
    steps:List[Step]=field(default_factory=lambda:[Step() for _ in range(64)]); length:int=16; direction:str='Forward'; transpose:int=0
    length_confirmed:bool=True
    binary_page_headers:List[str]=field(default_factory=list); binary_page_metadata:List[str]=field(default_factory=list)
    # Original variable-length page payloads, retained byte-for-byte for safe round trips.
    binary_page_payloads:List[str]=field(default_factory=list)
    automation:List[Dict]=field(default_factory=empty_lines)
    native_automation:Dict=field(default_factory=dict)
    native_raw_hex:str=''
    @property
    def can_duplicate(self):
        return self.length_confirmed and 1<=self.length<=32 and (not self.native_automation or self.native_automation.get('entry_count')==0)
    @property
    def can_duplicate_to_next_bar(self):
        # Unlike legacy duplicate(), this operation may grow Sequence Length itself.
        return self.length_confirmed and self.length<64 and any(step.notes for step in self.steps[:min(64,self.length)])
    def duplicate(self):
        n=self.length
        if not self.can_duplicate:raise ValueError('Dupl requires Length 1..32 and decoded Step Automation; native mapping PARTIAL')
        self.steps[n:n*2]=copy.deepcopy(self.steps[:n])
        for lane in self.automation:
            for key in ('values','fine_values','cc_values'):
                if key in lane:
                    values=lane[key]
                    while len(values)<64:values.append(None)
                    values[n:n*2]=copy.deepcopy(values[:n])
        self.length=n*2
    def duplicate_to_next_bar(self,steps_per_bar):
        if not self.can_duplicate_to_next_bar:raise ValueError('Dupl requires notes and room up to 64 steps')
        bar=max(1,int(steps_per_bar))
        last_note=next((i for i in range(min(64,self.length,len(self.steps))-1,-1,-1) if self.steps[i].notes),None)
        if last_note is None:raise ValueError('Dupl requires at least one note')
        source_len=((last_note//bar)+1)*bar
        if source_len>=64:raise ValueError('No next bar available for duplicate')
        copy_len=min(source_len,64-source_len)
        self.steps[source_len:source_len+copy_len]=copy.deepcopy(self.steps[:copy_len])
        for lane in self.automation:
            for key in ('values','fine_values','cc_values'):
                if key in lane:
                    values=lane[key]
                    while len(values)<64:values.append(None)
                    values[source_len:source_len+copy_len]=copy.deepcopy(values[:copy_len])
        self.length=max(self.length,min(64,source_len+copy_len))
    def fill64(self,source_len=None):
        n=max(1,min(64,int(source_len or self.length or 1))); base=[Step(**asdict(x)) for x in self.steps[:n]]
        for i in range(64): self.steps[i]=Step(**asdict(base[i%n]))
        for lane in self.automation:
            src=list(lane.get('values',[64]*64))[:n] or [64]; lane['values']=[src[i%len(src)] for i in range(64)]
            if 'cc_values' in lane:
                raw=list(lane['cc_values'])[:n] or [None];lane['cc_values']=[raw[i%len(raw)] for i in range(64)]
        self.length=64
@dataclass
class Preset:
    name:str='INIT'; number:Optional[int]=None; params:Dict[str,int]=field(default_factory=dict); sequence:Sequence=field(default_factory=Sequence); tags:List[str]=field(default_factory=list); category:str='My Presets'; source:str='local'
    def save(self,path):
        with open(path,'w',encoding='utf-8') as f: json.dump(asdict(self),f,ensure_ascii=False,indent=2)
@dataclass
class SongSlot: preset_path:Optional[str]=None; preset_name:str='EMPTY'
@dataclass
class Song:
    name:str='Untitled Song'; tempo:int=120; length:int=16; slots:List[SongSlot]=field(default_factory=lambda:[SongSlot() for _ in range(64)])
    def save(self,path):
        with open(path,'w',encoding='utf-8') as f: json.dump(asdict(self),f,ensure_ascii=False,indent=2)
    @classmethod
    def load(cls,path):
        with open(path,'r',encoding='utf-8') as f:d=json.load(f)
        s=cls(d.get('name','Untitled Song'),int(d.get('tempo',120)),int(d.get('length',16))); raw=d.get('slots',[])
        s.slots=[SongSlot(**x) for x in raw[:64]]+[SongSlot() for _ in range(max(0,64-len(raw)))]; return s
