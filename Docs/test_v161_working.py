from pathlib import Path
import inspect, tempfile
from types import SimpleNamespace
from app import App
import storage
from data_model import Preset

app=App(); app.withdraw(); app.update_idletasks()
try:
    app.midi.sysex=lambda *a,**k: True
    app.midi.send_cc=lambda *a,**k: True
    app.midi.bank_program=lambda *a,**k: True
    app._schedule_hardware_refresh=lambda *a,**k: None

    # Fixed UI scale presets and manual resize disabled.
    src=inspect.getsource(App._apply_ui_scale)
    for token in ["'50%':(640,360)", "'100%':(1280,720)", "'125%':(1600,900)", "'150%':(1920,1080)"]:
        assert token in src
    assert "resizable(False,False)" in src
    assert storage.DEFAULT.get('ui_scale')=='100%'

    # Contextual top bar: SYNTH uses synth algorithms, SEQ uses sequencer algorithms.
    top=inspect.getsource(App.topbar)
    assert "self.randomize_synth if self.page=='SYNTH' else self.seq_randomize" in top
    assert "self.init_patch if self.page=='SYNTH' else self.seq_clear_request" in top
    assert "if self.page in ('SYNTH','ARP + SEQUENCER')" in top

    # SEQ cleanup / layout.
    seq=inspect.getsource(App.draw_seq)
    assert "'Fill all 64 steps with sequences.'" in seq
    assert "'FILL'" in seq
    assert "'RESOLUTION'" not in seq
    assert "'STRAIGHT'" not in seq and "'TRIPLET'" not in seq and "'DOTTED'" not in seq
    assert "'COPY'" not in seq and "'PASTE'" not in seq and "'RANDOM'" not in seq
    assert "str(seq_len),9,MUTED" in seq
    confirm=inspect.getsource(App.seq_clear_request)
    assert "Initialize sequence?" in confirm and "('YES',yes)" in confirm and "('NO',no)" in confirm

    # Modulation Amount line is based at the modulation zero point, not parameter value.
    slider=inspect.getsource(App.slider)
    assert "zero=x+w/2" in slider and "zero=y+h/2" in slider
    assert "'modamount'" in slider
    hover=inspect.getsource(App.hover_motion)
    assert "after(400" in hover and "_show_mod_tooltip" in hover

    # Envelope marker uses a perceptual visual minimum only; real envelope function remains independent.
    marker=inspect.getsource(App._env_marker_position)
    env=inspect.getsource(App._env_level)
    assert "max(A0,.075)" in marker and "max(D0,.075)" in marker and "max(R0,.075)" in marker
    assert "max(A0,.075)" not in env

    # Library hardware horizontal navigation does not send Program Change on left/right.
    keys=inspect.getsource(App.keypress)
    assert "d=-230 if e.keysym=='Left' else 230" in keys

    # SONG tree root stays open, children toggle, and drop assignment has a metadata fallback.
    assert str(storage.PRESETS) in app.song_tree_expanded
    toggle=inspect.getsource(App._song_tree_toggle)
    assert "path==Path(storage.PRESETS)" in toggle
    release=inspect.getsource(App.release)
    assert "preset_name=name" in release and "using drag label" in release
    wheel=inspect.getsource(App.wheel)
    assert "self.song_folder_scroll" in wheel


    # SONG release path actually assigns a dropped preset to the target slot.
    with tempfile.TemporaryDirectory() as td:
        pp=Path(td)/'drop.unosyp'; pr=Preset(name='DROP TEST'); pr.save(pp)
        app.drag=(0,0,1,1,'songdrag',None,{'path':pp,'name':'DROP TEST'});app._lib_drag_started=True;app._lib_drag_origin=(0,0);app._lib_drag_pos=(10,10);app.song_mode='SONG'
        old_hit=app._hit_at;app._hit_at=lambda x,y:(0,0,100,100,'songcell',3,None)
        app.release(SimpleNamespace(x=0,y=0));app._hit_at=old_hit
        assert app.song.slots[3].preset_name=='DROP TEST' and app.song.slots[3].preset_path==str(pp)

    # Hardware panel wheel scroll is horizontal even when slot hitboxes are above the panel hitbox.
    app.page='LIBRARY';app.scale=1;app.ox=0;app.oy=0;app.lib_hscroll[1]=0
    app.hit=[(0,0,500,500,'libhwscroll',1,1000),(10,10,200,30,'hwslot',1,None)]
    app.wheel(SimpleNamespace(x=20,y=20,delta=-120,state=0))
    assert app.lib_hscroll[1]==140

    print('PASS v1.61 working GUI/software regression')
finally:
    app._closing=True
    try: app.midi.close()
    except Exception: pass
    try: app.destroy()
    except Exception: pass
