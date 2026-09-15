"""Read-only discovery adapted from the inherited UNO storage.py."""
from pathlib import Path
import sys

def default_root():
    documents=Path.home()/'Documents'
    if sys.platform.startswith('win'):
        import ctypes
        buf=ctypes.create_unicode_buffer(32768)
        if ctypes.windll.shell32.SHGetFolderPathW(None,5,None,0,buf)==0:documents=Path(buf.value)
    return documents/'IK Multimedia'/'UNO Synth Pro Editor'

def children(folder):
    try:
        return sorted((p for p in Path(folder).iterdir() if not p.is_symlink() and
            ((p.is_dir() and p.name.lower()!='songs') or (p.is_file() and p.suffix.lower()=='.unosyp'))),
            key=lambda p:(not p.is_dir(),p.name.lower()))
    except OSError:return []

class PresetLibrary:
    def __init__(self):self.names={}
    def capture(self,path):
        path=Path(path).resolve()
        if not path.is_file():raise ValueError('PRESET NOT FOUND')
        self.names[str(path)]=path.stem
        return str(path)
    def label(self,id):
        return Path(id).stem if Path(id).is_file() else 'PRESET NOT FOUND'
