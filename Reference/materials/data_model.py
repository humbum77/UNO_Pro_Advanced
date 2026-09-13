from dataclasses import dataclass,field,asdict
from typing import List,Dict,Optional
import json
@dataclass
class Step:
    notes:List[int]=field(default_factory=list); velocity:int=100; length:float=1.0; gate:int=0; accent:int=0; tie:bool=False; probability:int=100
    note_velocities:List[int]=field(default_factory=list); note_extras:List[int]=field(default_factory=list); control_raw:Optional[int]=None
@dataclass
class Sequence:
    steps:List[Step]=field(default_factory=lambda:[Step() for _ in range(64)]); length:int=16; direction:str='Forward'; transpose:int=0
    length_confirmed:bool=True
    binary_page_headers:List[str]=field(default_factory=list); binary_page_metadata:List[str]=field(default_factory=list)
    automation:List[Dict]=field(default_factory=lambda:[{'parameter':'CUTOFF 1','values':[64]*64} for i in range(4)])
    def fill64(self,source_len=None):
        n=max(1,min(64,int(source_len or self.length or 1))); base=[Step(**asdict(x)) for x in self.steps[:n]]
        for i in range(64): self.steps[i]=Step(**asdict(base[i%n]))
        for lane in self.automation:
            src=list(lane.get('values',[64]*64))[:n] or [64]; lane['values']=[src[i%len(src)] for i in range(64)]
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
