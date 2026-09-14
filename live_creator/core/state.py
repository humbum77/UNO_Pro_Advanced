"""Single JSON state, no embedded assets; transactional validation on load."""
import json,os,tempfile
from pathlib import Path
from .session import Session
from .arrangement import PresetBlock

def encode(session):
    return {'format':'LiveCreatorState','version':2,'selected':session.selected,
            'global_settings':session.global_settings,'controller_settings':session.controller_settings,
            'pads':[{'name':s.name,'color':s.color,'tempo':s.timeline.tempo,'delay':s.delay,
                     'colors':s.colors,'loop':s.timeline.loop_range,'markers':s.timeline.markers,
                     'blocks':[{'id':b.id,'preset':b.preset,'length':b.length,'color':b.color,'parameters':b.parameters} for b in s.timeline.blocks]} for s in session.pads]}

def decode(data):
    if data.get('format')!='LiveCreatorState' or data.get('version') not in (1,2) or len(data['pads'])!=64:raise ValueError('Invalid Live Creator state')
    session=Session();session.select_pad(data.get('selected',0))
    session.global_settings=data.get('global_settings',{});session.controller_settings=data.get('controller_settings',{})
    if not isinstance(session.global_settings,dict) or not isinstance(session.controller_settings,dict):raise ValueError('Invalid settings')
    if not isinstance(session.global_settings.get('library_root',''),str):raise ValueError('Invalid library root')
    def color(value):
        if not isinstance(value,str) or len(value)!=7 or value[0]!='#' or any(c not in '0123456789abcdefABCDEF' for c in value[1:]):raise ValueError('Invalid color')
        return value
    for song,d in zip(session.pads,data['pads']):
        if not isinstance(d['name'],str) or len(d['name'])>256:raise ValueError('Invalid name')
        song.name=d['name'];song.color=color(d['color']);song.timeline.set_tempo(d['tempo'])
        if d['delay'] not in (0,5,10,15,30,45,60):raise ValueError('Invalid delay')
        song.delay=d['delay'];song.colors={str(k):color(v) for k,v in d['colors'].items()}
        blocks=[]
        for b in d['blocks']:
            if not isinstance(b['id'],str) or b['preset'] is not None and not isinstance(b['preset'],str):raise ValueError('Invalid block')
            if not isinstance(b.get('parameters',{}),dict):raise ValueError('Invalid block parameters')
            blocks.append(PresetBlock(b['id'],b['preset'],b['length'],color(b['color']) if b.get('color') else None,b.get('parameters',{})))
        if len({b.id for b in blocks})!=len(blocks):raise ValueError('Duplicate block ID')
        song.timeline.commit(blocks)
        for step,label in d.get('markers',{}).items():song.timeline.set_marker(int(step),label)
        loop=d.get('loop')
        if loop is not None:
            if len(loop)!=2 or not all(type(x)is int for x in loop) or not 1<=loop[0]<=loop[1]<=song.timeline.length:raise ValueError('Invalid loop')
            song.timeline.loop_range=tuple(loop)
    return session

def load(path):return decode(json.loads(Path(path).read_text(encoding='utf-8')))
def save(path,session):
    path=Path(path);payload=json.dumps(encode(session),ensure_ascii=False,indent=2)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:stream.write(payload)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
