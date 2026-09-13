from pathlib import Path
import inspect
from app import App, IK_HEADER, MATRIX_DESTINATIONS
from data_model import Step
import storage

app=App(); app.withdraw(); app.update_idletasks()
try:
    # no hardware side effects
    sent=[]
    app.midi.sysex=lambda d: sent.append(bytes(d)) or True
    app.midi.send_cc=lambda *a,**k: True
    app.midi.bank_program=lambda *a,**k: True
    app.midi.start=lambda: True
    app.midi.stop=lambda: True
    app._schedule_hardware_refresh=lambda *a,**k: None

    # ARP reverse command uses the editor->UNO frame actually captured from official editor traffic.
    app.arp_on=False
    app.toggle_arp_on(); app.toggle_arp_on()
    assert sent[-2] == IK_HEADER+bytes([0x35,0x00,0x01,0xF7])
    assert sent[-1] == IK_HEADER+bytes([0x35,0x00,0x00,0xF7])

    # New software notes occupy a full step by default.
    assert Step().length == 1.0

    # CLEAR button is wired to confirmation, not immediate clear.
    src=inspect.getsource(App.draw_seq)
    assert "self.seq_clear_request" in src or "seq_clear_request" in inspect.getsource(App.topbar)

    # Matrix source/destination use large picker mode and do not wheel-scroll underneath.
    h=(600,700,315,32,'choice','MDST0',MATRIX_DESTINATIONS)
    app._open_dropdown(h,'MDST0',MATRIX_DESTINATIONS)
    assert app.open_dropdown and app.open_dropdown.get('picker') is True
    before=app.dropdown_scroll
    app._scroll_dropdown(1)
    assert app.dropdown_scroll==before

    # Folder pane widened to prevent folder names from spilling into preset viewer.
    src=inspect.getsource(App._draw_local_panel)
    assert 'tree_w=250' in src

    # Hardware slot renderer rejects partially visible columns so text cannot cross panel edge.
    src=inspect.getsource(App._draw_uno_slots)
    assert 'xx < x+6 or xx+col_w > x+w-6' in src

    # SONG preset rows initiate drag-and-drop into song slots.
    click_src=inspect.getsource(App.click)
    rel_src=inspect.getsource(App.release)
    assert "'songdrag'" in click_src and "target[4]=='songcell'" in rel_src

    # ADSR drag now performs one redraw path after grouped DS updates rather than two set_value redraws.
    env_src=inspect.getsource(App._drag_env_point)
    assert 'self.set_value(' not in env_src and "updates=[" in env_src

    print('PASS v1.60 working GUI/software regression')
finally:
    app._closing=True
    try: app.midi.close()
    except Exception: pass
    try: app.destroy()
    except Exception: pass
