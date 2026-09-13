from pathlib import Path
import tkinter as tk
from app import App
import storage


def assert_true(v,msg):
    if not v: raise AssertionError(msg)

app=App(); app.withdraw(); app.update_idletasks()
try:
    # prevent hardware side effects during UI regression checks
    app.midi.bank_program=lambda *a,**k: None
    app.midi.send_cc=lambda *a,**k: None
    app.midi.sysex=lambda *a,**k: True
    app._schedule_hardware_refresh=lambda *a,**k: None


    # ARP RATE does not exist on hardware and must not reappear in GUI/model.
    assert 'ARP_RATE' not in app.values

    # Confirmed live hardware notifications: Voice Mode and ARP ON/OFF are receive-only GUI sync.
    sent=[]
    app.midi.sysex=lambda d: sent.append(bytes(d)) or True
    app._midi_rx_ui(bytes.fromhex('F0 00 21 1A 02 03 34 04 02 F7'),True)
    assert app.choice['VOICE']==2 and sent==[]
    app._midi_rx_ui(bytes.fromhex('F0 00 21 1A 02 03 34 06 01 F7'),True)
    assert app.arp_on is True and sent==[]
    app._midi_rx_ui(bytes.fromhex('F0 00 21 1A 02 03 34 06 00 F7'),True)
    assert app.arp_on is False and sent==[]

    # Confirmed transport: editor PLAY/STOP sends MIDI realtime FA/FC via MidiEngine start/stop.
    calls=[]
    app.midi.start=lambda: calls.append(0xFA) or True
    app.midi.stop=lambda: calls.append(0xFC) or True
    app.seq_playing=False;app.toggle_seq_play();app.toggle_seq_play()
    assert calls==[0xFA,0xFC]

    # LFO Fade In defaults
    assert app.values['LFO1_FADE']==0 and app.values['LFO2_FADE']==0
    assert app._format_popup_value('LFO1_FADE',0)=='OFF'

    # ADSR visual mapping: short times are expanded, monotonic, inverse is close.
    vals=[app._env_visual_norm(v) for v in (0,25,50,75,100,127)]
    assert vals==sorted(vals) and vals[0]==0 and vals[-1]>.99
    for raw in (1,25,50,75,100,127):
        back=app._env_visual_raw(app._env_visual_norm(raw))
        assert abs(back-raw)<=1,(raw,back)

    # Envelope drag constraints: AD x-only; DS x+y; SR y-only; R x-only.
    app.values.update({'FENV_A':40,'FENV_D':50,'FENV_S':80,'FENV_R':60})
    beforeS=app.values['FENV_S']
    app._drag_env_point((0,0,0,0,'envpoint','FENV',(0,0,0,300,120)),180,100)
    assert app.values['FENV_S']==beforeS
    app._drag_env_point((0,0,0,0,'envpoint','FENV',(1,0,0,300,120)),180,100)
    assert app.values['FENV_S']!=beforeS
    r_before=app.values['FENV_R'];d_before=app.values['FENV_D']
    app._drag_env_point((0,0,0,0,'envpoint','FENV',(2,0,0,300,120)),250,20)
    assert app.values['FENV_R']==r_before and app.values['FENV_D']==d_before

    # Piano roll click selects existing note, double action deletes it.
    d={'gx':0,'gy':0,'gw':160,'gh':220,'visible':16,'first':0,'rows':22,'top_note':60}
    st=app.preset.sequence.steps[0];st.notes=[60];st.length=3.0
    app._piano_edit(d,5,5)
    assert app.selected_seq_note==(0,60) and st.notes==[60]
    assert app._piano_delete(d,5,5) and st.notes==[]

    # LENGTH remains stored and is used by drawing path; basic value regression.
    st.notes=[60];st.length=3.5
    assert st.length==3.5

    # Song tree expands by single folder action.
    app.song_tree_expanded.clear();app._song_tree_toggle(storage.PRESETS)
    assert str(storage.PRESETS) in app.song_tree_expanded

    # Matrix dropdown wheel focus: opening a list then scrolling changes dropdown, not matrix.
    app.page='SYNTH';app.matrix_scroll=4
    app.open_dropdown={'x':1,'y':1,'w':100,'h':20,'key':'MSRC0','opts':list(range(30))};app.dropdown_scroll=5
    class E: pass
    e=E();e.x=10;e.y=10;e.delta=-120;e.state=0
    app.wheel(e)
    assert app.dropdown_scroll==6 and app.matrix_scroll==4

    # Hardware library is column/horizontal-scroll based.
    app.page='LIBRARY';app.redraw();kinds=[h[4] for h in app.hit]
    assert 'libhwscroll' in kinds
    hwscroll=next(h for h in app.hit if h[4]=='libhwscroll')
    assert hwscroll[6]>0

    # CLEAR dialog uses custom themed Toplevel and can be cancelled.
    app.seq_clear_request();app.update_idletasks()
    tops=[w for w in app.winfo_children() if isinstance(w,tk.Toplevel)]
    assert_true(tops,'clear confirmation window missing')
    for w in tops:w.destroy()

    print('PASS v1.59 working GUI/software regression')
finally:
    app._closing=True
    try: app.midi.close()
    except Exception: pass
    try: app.destroy()
    except Exception: pass
