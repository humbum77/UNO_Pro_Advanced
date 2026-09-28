"""Persistent UNO preset-name cache shared by the main Library and LIVE browser."""
from pathlib import Path
import json, os, tempfile
from datetime import datetime, timezone


def _root():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData'/'Local')))/'UnoLive'


CACHE_FILE=_root()/'hardware_preset_names.json'


def load_cache(path=CACHE_FILE):
    try:
        document=json.loads(Path(path).read_text(encoding='utf-8'))
        names=document.get('names', document) if isinstance(document,dict) else {}
        clean={int(slot):str(name) for slot,name in names.items()
               if str(slot).isdigit() and 1<=int(slot)<=256 and isinstance(name,str)}
        verified=document.get('verified_slots',[]) if isinstance(document,dict) else []
        missing=document.get('missing_slots',[]) if isinstance(document,dict) else []
        return {'version':2,'names':clean,
                'verified_slots':sorted({int(n) for n in verified if str(n).isdigit() and 1<=int(n)<=256}),
                'missing_slots':sorted({int(n) for n in missing if str(n).isdigit() and 1<=int(n)<=256}),
                'last_scan_started':str(document.get('last_scan_started','')) if isinstance(document,dict) else '',
                'last_scan_completed':str(document.get('last_scan_completed','')) if isinstance(document,dict) else ''}
    except (OSError,UnicodeError,ValueError,TypeError,json.JSONDecodeError):
        return {'version':2,'names':{},'verified_slots':[],'missing_slots':[],
                'last_scan_started':'','last_scan_completed':''}


def load_names(path=CACHE_FILE):
    return load_cache(path)['names']


def save_cache(names,path=CACHE_FILE,verified_slots=(),missing_slots=(),
               last_scan_started='',last_scan_completed=''):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data={'version':2,'names':{str(slot):str(name) for slot,name in sorted(names.items())
                              if 1<=int(slot)<=256 and isinstance(name,str)},
          'verified_slots':sorted({int(n) for n in verified_slots if 1<=int(n)<=256}),
          'missing_slots':sorted({int(n) for n in missing_slots if 1<=int(n)<=256}),
          'last_scan_started':str(last_scan_started or ''),
          'last_scan_completed':str(last_scan_completed or '')}
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=str(path.parent))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        try:
            if os.path.exists(tmp):os.unlink(tmp)
        except OSError:pass


def save_names(names,path=CACHE_FILE):
    """Backward-compatible name update which retains scan verification metadata."""
    old=load_cache(path)
    save_cache(names,path,old['verified_slots'],old['missing_slots'],
               old['last_scan_started'],old['last_scan_completed'])


def utc_now():
    return datetime.now(timezone.utc).isoformat()
