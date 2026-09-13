"""Minimal internal ZIP container; raw preset bytes never decoded or rewritten."""
import hashlib,json,os,tempfile,zipfile
from pathlib import Path
from live_creator.core.arrangement import Arrangement
from live_creator.devices.uno.library import PresetLibrary

def save(path, model, library):
    used={b.preset for b in model.blocks if b.preset is not None}
    manifest={'format':'live-creator','version':1,'tempo':model.tempo,
              'blocks':[{'preset_id':b.preset,'length':b.length} for b in model.blocks],
              'names':{id:library.names[id] for id in used}}
    path=Path(path)
    fd,tmp=tempfile.mkstemp(dir=path.parent,suffix='.tmp');os.close(fd)
    try:
        with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('manifest.json',json.dumps(manifest))
            for id in used:
                raw=library.assets[id]
                if hashlib.sha256(raw).hexdigest()!=id:raise ValueError('Preset hash mismatch')
                z.writestr('presets/'+id+'.unosyp',raw)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def load(path):
    model=Arrangement();library=PresetLibrary()
    with zipfile.ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist())>32*1024*1024:raise ValueError('Song is too large')
        m=json.loads(z.read('manifest.json'))
        if m.get('format')!='live-creator' or m.get('version')!=1:raise ValueError('Unsupported song format')
        model.set_tempo(m['tempo'])
        for b in m['blocks']:
            id=b['preset_id']
            if id is not None:
                if not isinstance(id,str) or len(id)!=64 or any(c not in '0123456789abcdef' for c in id):raise ValueError('Invalid preset ID')
                raw=z.read('presets/'+id+'.unosyp')
                if hashlib.sha256(raw).hexdigest()!=id:raise ValueError('Preset hash mismatch')
                library.assets[id]=raw;library.names[id]=str(m['names'][id])
            model.insert(len(model.blocks),id,b['length'])
    return model,library
