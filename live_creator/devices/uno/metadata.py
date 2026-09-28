"""Read-only access to UNO Pro Advanced preset color-tag metadata."""
from pathlib import Path
import hashlib,json,os
TAG_COLORS=('#e34b4b','#ed8b32','#e2c744','#63b85b','#4d9fdf','#786bd6','#c05ac4')
TAG_NAMES=('RED','ORANGE','YELLOW','GREEN','BLUE','VIOLET','MAGENTA')

def _documents():
    p=Path.home()/'Documents'
    if os.name=='nt':
        try:
            import ctypes
            b=ctypes.create_unicode_buffer(32768)
            if ctypes.windll.shell32.SHGetFolderPathW(None,5,None,0,b)==0:p=Path(b.value)
        except Exception:pass
    return p

def metadata_path():
    local=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData'/'Local')))/'UnoLive'/'uno_pro_advanced_metadata.json'
    legacy=_documents()/'IK Multimedia'/'UNO Synth Pro Editor'/'uno_pro_advanced_metadata.json'
    return local if local.exists() else legacy

def _db():
    # Merge legacy first, then current UnoLive metadata. This keeps existing tags
    # visible after UI-only changes and lets the current database override them.
    result={}
    legacy=_documents()/'IK Multimedia'/'UNO Synth Pro Editor'/'uno_pro_advanced_metadata.json'
    current=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData'/'Local')))/'UnoLive'/'uno_pro_advanced_metadata.json'
    for source in (legacy,current):
        try:
            d=json.loads(source.read_text(encoding='utf-8'))
            if isinstance(d,dict):result.update(d)
        except Exception:pass
    return result

def key(path):
    path=Path(path)
    try:return hashlib.sha1(path.read_bytes()).hexdigest()
    except OSError:return 'path:'+str(path.resolve())

def tags_for(path):
    v=_db().get(key(path),{});return tuple(i for i in v.get('colors',[]) if isinstance(i,int) and 0<=i<7)

def favorite_for(path):
    v=_db().get(key(path),{});return bool(v.get('favorite',False))


def order_for(path):
    v=_db().get(key(path),{});o=v.get('order',None);return int(o) if isinstance(o,(int,float)) else None
