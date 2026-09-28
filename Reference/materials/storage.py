from pathlib import Path
import json,logging,os,sys,tempfile
from data_model import *

logger=logging.getLogger(__name__)

def _documents_folder():
    # Windows CSIDL_PERSONAL resolves the user's actual (including redirected/OneDrive) Documents folder.
    if sys.platform.startswith('win'):
        try:
            import ctypes
            buf=ctypes.create_unicode_buffer(32768)
            # CSIDL_PERSONAL = 5, SHGFP_TYPE_CURRENT = 0
            hr=ctypes.windll.shell32.SHGetFolderPathW(None,5,None,0,buf)
            if hr==0 and buf.value:return Path(buf.value)
        except Exception as e:
            logger.warning('Windows Documents lookup failed: %s',e)
    return Path.home()/'Documents'

DOCUMENTS=_documents_folder()
ROOT=DOCUMENTS/'IK Multimedia'/'UNO Synth Pro Editor'
PRESETS=ROOT
SONGS=ROOT/'songs'
SETTINGS=ROOT/'settings.json'
DEFAULT={'midi_in':'UNO Synth Pro','midi_out':'UNO Synth Pro','midi_controller':'Off','midi_in_channel':1,'midi_out_channel':1,'midi_clock':'Off','sync':'Internal','pr_change':True,'midi_interface':'Auto','pitch_bend_range':2,'keyboard_visible':False,'live_delay':0,'ui_scale':'125%','live_slots':[None]*64}
_preset_cache=None
_preset_cache_sig=None

def ensure_dirs():
    ROOT.mkdir(parents=True,exist_ok=True);SONGS.mkdir(parents=True,exist_ok=True)

def load_settings():
    d=dict(DEFAULT);d['live_slots']=list(DEFAULT['live_slots'])
    try:
        if SETTINGS.exists():d.update(json.loads(SETTINGS.read_text(encoding='utf-8')))
    except (OSError,json.JSONDecodeError,TypeError,ValueError) as e:logger.warning('Failed to load settings %s: %s',SETTINGS,e)
    slots=d.get('live_slots')
    d['live_slots']=(list(slots[:64])+[None]*64)[:64] if isinstance(slots,list) else [None]*64
    return d

def save_settings(d):
    ensure_dirs()
    text=json.dumps(d,ensure_ascii=False,indent=2)
    fd,tmp=tempfile.mkstemp(prefix='settings.',suffix='.tmp',dir=str(ROOT))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(text);f.flush();os.fsync(f.fileno())
        os.replace(tmp,SETTINGS)
    finally:
        try:
            if os.path.exists(tmp):os.unlink(tmp)
        except OSError:pass

def _safe(s):return ''.join(c for c in s if c not in '<>:"/\\|?*').strip() or 'Untitled'

def invalidate_preset_cache():
    global _preset_cache,_preset_cache_sig
    _preset_cache=None;_preset_cache_sig=None

def _scan_signature():
    if not PRESETS.exists():return ()
    try:
        return tuple(sorted((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in PRESETS.rglob('*.unosyp') if SONGS not in p.parents))
    except OSError:return ()

def _all_presets():
    global _preset_cache,_preset_cache_sig
    sig=_scan_signature()
    if _preset_cache is not None and sig==_preset_cache_sig:return _preset_cache
    out=[]
    for p,_,_ in sig:
        p=Path(p)
        try:
            d=json.loads(p.read_text(encoding='utf-8'));n=d.get('name',p.stem);c=d.get('category','My Presets');t=d.get('tags',[])
        except (OSError,UnicodeDecodeError,json.JSONDecodeError,TypeError,ValueError):
            n=p.stem;c='My Presets';t=[]
        out.append((n,c,t,p))
    _preset_cache=sorted(out,key=lambda x:x[0].lower());_preset_cache_sig=sig
    return _preset_cache

def list_presets(category='All',query=''):
    q=query.lower().strip();out=[]
    for n,c,t,p in _all_presets():
        if (category=='All' or c==category) and (not q or q in (' '.join([n,c,*t]).lower())):out.append((n,c,t,p))
    return out

def categories():return ['All']+sorted({x[1] for x in _all_presets() if x[1]!='All'}|{'My Presets'})

def save_preset(preset,category=None):
    ensure_dirs()
    if category:preset.category=category
    p=PRESETS/(_safe(preset.name)+'.unosyp');i=2
    while p.exists():p=PRESETS/f'{_safe(preset.name)} {i}.unosyp';i+=1
    preset.save(p);invalidate_preset_cache();return p

def load_preset(path):
    d=json.loads(Path(path).read_text(encoding='utf-8'));sd=d.get('sequence',{});seq=Sequence(length=int(sd.get('length',16)),direction=sd.get('direction','Forward'),transpose=int(sd.get('transpose',0)))
    ss=sd.get('steps',[]);seq.steps=[Step(**x) for x in ss[:64]]+[Step() for _ in range(max(0,64-len(ss)))];seq.automation=sd.get('automation',seq.automation)
    return Preset(d.get('name','INIT'),d.get('number'),d.get('params',{}),seq,d.get('tags',[]),d.get('category','My Presets'),d.get('source','local'))



def load_binary_unosyp_state(path):
    """Read-only decode of the 260-byte synth/current-state embedded in .unosyp."""
    from unosyp_state_decoder import decode_unosyp_state
    return decode_unosyp_state(path)

def load_binary_unosyp_sequence(path):
    """Read-only decode of the confirmed 1081-byte UNO .unosyp sequencer."""
    from unosyp_seq_decoder import parse_unosyp
    info=parse_unosyp(Path(path).read_bytes())
    if not info.get('supported_sequence_variant'):
        return None
    seq=Sequence();seq.length_confirmed=False
    seq.binary_page_headers=[p.get('header_hex','') for p in info.get('pages',[])]
    seq.binary_page_metadata=[p.get('metadata_hex','') for p in info.get('pages',[])]
    active_last=0
    for decoded in info.get('steps',[])[:64]:
        idx=int(decoded.get('step',0))-1
        if not 0<=idx<64:continue
        notes=[];vels=[];extras=[]
        for voice in decoded.get('voices',[])[:3]:
            if voice.get('empty'):continue
            note=int(voice.get('note_raw',255))
            if not 0<=note<=127:continue
            notes.append(note);vels.append(max(0,min(127,int(voice.get('velocity',100)))))
            extras.append(int(voice.get('extra_raw',255))&0xFF)
        st=seq.steps[idx];st.notes=notes;st.note_velocities=vels;st.note_extras=extras
        st.control_raw=int(decoded.get('control_raw',0))&0xFF
        if vels:st.velocity=vels[0]
        if notes:active_last=idx+1
    seq.length=max(16,active_last)
    return seq

def child_folders(folder):
    """Direct child directories for the LOCAL library browser."""
    try:
        folder=Path(folder)
        if not folder.exists():
            return []
        out=[]
        songs_resolved=None
        try:
            songs_resolved=SONGS.resolve()
        except OSError:
            pass
        for p in folder.iterdir():
            if not p.is_dir():
                continue
            if songs_resolved is not None:
                try:
                    if p.resolve()==songs_resolved:
                        continue
                except OSError:
                    pass
            out.append(p)
        return sorted(out,key=lambda p:p.name.lower())
    except OSError as e:
        logger.warning('Failed to list child folders %s: %s',folder,e)
        return []

def local_folders():
    """Top-level LOCAL preset folders for the main preset selector tree."""
    return child_folders(PRESETS)

def list_songs():
    if not SONGS.exists():return []
    return sorted(SONGS.glob('*.unosong'),key=lambda p:p.stem.lower())

def save_song(song):
    ensure_dirs();p=SONGS/(_safe(song.name)+'.unosong');song.save(p);return p

# UNO Pro Advanced local-only metadata. Never written into UNO preset files or sent to hardware.
METADATA=ROOT/'uno_pro_advanced_metadata.json'

def _metadata_key(path):
    import hashlib
    path=Path(path)
    try:return hashlib.sha1(path.read_bytes()).hexdigest()
    except OSError:return 'path:'+str(path.resolve())

def _load_metadata_db():
    try:
        d=json.loads(METADATA.read_text(encoding='utf-8'))
        return d if isinstance(d,dict) else {}
    except Exception:return {}

def _save_metadata_db(d):
    ensure_dirs();fd,tmp=tempfile.mkstemp(prefix='metadata.',suffix='.tmp',dir=str(ROOT))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,METADATA)
    finally:
        try:
            if os.path.exists(tmp):os.unlink(tmp)
        except OSError:pass

def get_preset_metadata(path):
    v=_load_metadata_db().get(_metadata_key(path),{})
    return {'favorite':bool(v.get('favorite',False)),'colors':[int(i) for i in v.get('colors',[]) if isinstance(i,int) and 0<=i<7], 'order':v.get('order',None)}

def set_preset_metadata(path,meta):
    d=_load_metadata_db();entry={'favorite':bool(meta.get('favorite',False)),'colors':sorted(set(int(i) for i in meta.get('colors',[]) if 0<=int(i)<7))};order=meta.get('order',None);entry['order']=int(order) if isinstance(order,(int,float)) else None;d[_metadata_key(path)]=entry;_save_metadata_db(d)
