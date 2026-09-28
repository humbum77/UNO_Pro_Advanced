"""Persistent application-side layout for the UNO hardware bank.

The device catalog and the staged layout are deliberately separate.  GET
replaces the physical snapshot; LOCAL -> Hardware and Hardware -> Hardware
operations only modify this staged document until SEND is pressed.
"""
from pathlib import Path
import json, os, tempfile


def _root():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData'/'Local')))/'UnoLive'


BANK_FILE=_root()/'hardware_bank_stage.json'
CACHE_DIR=_root()/'hardware_presets'


def physical_entry(slot,name=''):
    return {'name':str(name),'kind':'device','source_slot':int(slot),'path':'','dirty':False}


def local_entry(path,name=None):
    source=Path(path)
    return {'name':str(name or source.stem),'kind':'local','source_slot':None,
            'path':str(source),'dirty':True}


def _clean_entry(slot,value):
    if not isinstance(value,dict):return physical_entry(slot,'')
    kind=value.get('kind','device')
    if kind not in ('device','local','cache'):kind='device'
    source=value.get('source_slot')
    try:source=int(source) if source is not None else None
    except (TypeError,ValueError):source=None
    if source is not None and not 1<=source<=256:source=None
    return {'name':str(value.get('name','')),'kind':kind,'source_slot':source,
            'path':str(value.get('path','')),'dirty':bool(value.get('dirty',False))}


def load_bank(names=None,path=BANK_FILE):
    names=dict(names or {})
    try:
        document=json.loads(Path(path).read_text(encoding='utf-8'))
        raw=document.get('slots',{}) if isinstance(document,dict) else {}
    except (OSError,UnicodeError,ValueError,TypeError,json.JSONDecodeError):raw={}
    result={}
    for slot in range(1,257):
        value=raw.get(str(slot)) if isinstance(raw,dict) else None
        result[slot]=_clean_entry(slot,value) if value is not None else physical_entry(slot,names.get(slot,''))
    return result


def save_bank(entries,path=BANK_FILE):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data={'version':1,'slots':{str(slot):_clean_entry(slot,entries.get(slot,{}))
                              for slot in range(1,257)}}
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=str(path.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp):os.unlink(tmp)
        except OSError:pass


def reset_from_catalog(names,path=BANK_FILE):
    entries={slot:physical_entry(slot,names.get(slot,'')) for slot in range(1,257)}
    save_bank(entries,path);return entries

