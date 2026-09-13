from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
DOCS=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

import storage
from data_model import Sequence
from protocol_map import IK_HEADER, ARP_SYSEX
from unosyp_state_decoder import (
    decode_file_state_raw,
    encode_raw_as_0x37_payload,
    decode_0x37_raw,
    build_virtual_0x37,
    decode_extended_preset_fields,
)


def assert_eq(got, expected, label):
    if got != expected:
        raise AssertionError(f'{label}: got {got!r}, expected {expected!r}')


def test_state_roundtrip_all_files():
    for name in ('test2.unosyp','test3.unosyp','test4.unosyp','test5.unosyp'):
        data=(DOCS/name).read_bytes()
        raw=decode_file_state_raw(data)
        frame=build_virtual_0x37(data)
        assert_eq(len(raw),260,f'{name} raw size')
        assert_eq(len(frame),309,f'{name} virtual 0x37 size')
        assert_eq(decode_0x37_raw(frame),raw,f'{name} raw 0x37 roundtrip')
        assert_eq(len(encode_raw_as_0x37_payload(raw)),298,f'{name} packed 0x37 size')
        state=storage.load_binary_unosyp_state(DOCS/name)
        assert_eq(len(state['resolved']),82,f'{name} resolved mapper fields')
        assert_eq(len(state['unresolved']),1,f'{name} unresolved mapper fields')
        ext=state['extended']
        assert_eq(ext.get('voice_mode'),1,f'{name} voice read-side candidate')
        assert_eq(ext.get('arp_direction'),0,f'{name} ARP direction')
        assert_eq(ext.get('arp_range'),1,f'{name} ARP range')
        assert_eq(ext.get('arp_pattern'),0xFFFF,f'{name} ARP pattern')


def test_sequence_variants():
    expected={
        'test2.unosyp':[(1,[61],[37],[1])],
        'test3.unosyp':[(1,[61],[37],[1]),(2,[60],[42],[1])],
        'test4.unosyp':[(2,[60],[42],[1])],
    }
    for name, exp in expected.items():
        seq=storage.load_binary_unosyp_sequence(DOCS/name)
        if seq is None:
            raise AssertionError(f'{name}: expected supported 1081-byte sequence')
        got=[(i+1,st.notes,st.note_velocities,st.note_extras) for i,st in enumerate(seq.steps) if st.notes]
        assert_eq(got,exp,f'{name} decoded sequence')
    if storage.load_binary_unosyp_sequence(DOCS/'test5.unosyp') is not None:
        raise AssertionError('test5.unosyp 1084-byte variant must remain sequence-unsupported')


def test_matrix_slot59_cross_boundary_and_fade_lock():
    raw=bytearray(260)
    raw[188:208]=bytes.fromhex(
        '60 03 C0 21 20 05 E0 43 00 04 40 21 A2 03 40 02 00 00 00 00'
    )
    matrix=decode_extended_preset_fields(raw)['matrix']
    got=[(matrix[i]['destination'],matrix[i]['source'],matrix[i]['amount_raw']) for i in range(4)]
    assert_eq(got,[(27,1,14),(41,2,31),(32,17,10),(29,0,18)],'factory slot59 matrix routes')
    assert_eq([matrix[i]['fade_raw'] for i in range(4)],[0,0,0,0],'slot59 fade raw')


def test_headless_app_paths():
    from app import App, MATRIX_SOURCES, MATRIX_DESTINATIONS

    class FakeMidi:
        def __init__(self):
            self.sent=[]
            self.bank=[]
        def sysex(self,msg):
            self.sent.append(bytes(msg));return True
        def send_cc(self,*args):
            self.sent.append(('cc',)+tuple(args));return True
        def bank_program(self,n):
            self.bank.append(int(n));return True
        def read_state(self):return True
        def read_preset_name(self,n):return True
        def start(self):return True
        def stop(self):return True
        def note_on(self,*args):return True
        def note_off(self,*args):return True
        def close(self):return None
        def inputs(self):return []
        def outputs(self):return []

    app=App()
    try:
        fake=FakeMidi();app.midi=fake

        # 1081: synth state + confirmed sequence.
        if not app.load_local_preset(DOCS/'test2.unosyp',preview=False):
            raise AssertionError('app failed to load test2 binary preset')
        assert_eq(app.sequence_origin,'LOCAL_BINARY_1081','test2 sequence source')
        assert_eq(app.values['OSC1_WAVE'],42,'test2 OSC1 wave')
        assert_eq(app.values['F1_CUTOFF'],127,'test2 filter cutoff')
        assert_eq(app.choice['VOICE'],1,'test2 Voice read-side')
        assert_eq(app.choice['ARP_MODE'],0,'test2 ARP direction')
        assert_eq(app.values['ARP_RANGE'],'1 OCT','test2 ARP range')
        if not all(app.arp_trig):raise AssertionError('test2 ARP pattern should be all on')
        assert_eq(app.values['MSRC0'],MATRIX_SOURCES[0],'test2 matrix source')
        assert_eq(app.values['MDST0'],MATRIX_DESTINATIONS[0],'test2 matrix destination')

        # Fade raw is deliberately not mapped into GUI MFADE until scale is proven.
        app.values['MFADE0']=17
        app._apply_extended_preset_fields({'matrix':[{'source':1,'destination':2,'fade_raw':777}]})
        assert_eq(app.values['MFADE0'],17,'matrix Fade In remains unmapped')

        # 1084: state is usable, sequence must not be presented as decoded.
        if not app.load_local_preset(DOCS/'test5.unosyp',preview=False):
            raise AssertionError('app failed to load test5 state-only binary preset')
        assert_eq(app.sequence_origin,'LOCAL_STATE_ONLY','test5 sequence source')
        if any(st.notes for st in app.preset.sequence.steps):
            raise AssertionError('test5 unsupported sequence variant must not create notes')

        # Hardware selection explicitly clears stale local sequence and marks 0x37 as state-only.
        app.load_local_preset(DOCS/'test3.unosyp',preview=False)
        if not any(st.notes for st in app.preset.sequence.steps):
            raise AssertionError('precondition: test3 must contain sequence notes')
        app._select_hw_preset(2)
        assert_eq(app.sequence_origin,'HARDWARE_STATE_ONLY','hardware sequence source')
        if any(st.notes for st in app.preset.sequence.steps):
            raise AssertionError('stale local sequence survived hardware preset selection')
        if '64 STEPS NOT READ' not in app._sequence_source_label():
            raise AssertionError('hardware sequence warning label missing')

        # 0x37 applies GUI state without MIDI echo.
        fake.sent.clear()
        frame=build_virtual_0x37((DOCS/'test2.unosyp').read_bytes())
        app.preset_source='HARDWARE'
        app._midi_rx_ui(frame,True)
        assert_eq(fake.sent,[],'0x37 receive MIDI echo')
        if 'hardware sequence not read' not in app.status:
            raise AssertionError('0x37 status does not identify missing sequence')

        # Live ARP 0x3E receive: direction, range, pattern.
        app._midi_rx_ui(IK_HEADER+bytes([0x3E,0x00,0x00,0x07,0xF7]),True)
        assert_eq(app.choice['ARP_MODE'],7,'ARP 0x3E direction')
        app._midi_rx_ui(IK_HEADER+bytes([0x3E,0x00,0x01,0x04,0xF7]),True)
        assert_eq(app.values['ARP_RANGE'],'4 OCT','ARP 0x3E range')
        logical_mask=0x1101
        payload=bytes([logical_mask&0x7F,(logical_mask>>7)&0x7F,(logical_mask>>14)&0x03])
        app._midi_rx_ui(IK_HEADER+bytes([0x3E,0x00,0x02])+payload+bytes([0xF7]),True)
        got_mask=sum((1<<i) for i,v in enumerate(app.arp_trig) if v)
        assert_eq(got_mask,logical_mask,'ARP 0x3E pattern')

        # Outgoing ARP Pattern 0x3C exact observed format.
        app.arp_trig=[False]*16;fake.sent.clear();app.toggle_arp(0)
        expected=IK_HEADER+bytes([0x3C,0x00,0x02,0x01,0x00,0x00,0xF7])
        assert_eq(fake.sent,[expected],'ARP pattern 0x3C send')

        # Range writer sends hardware-observed native values 1..4, not value-1.
        fake.sent.clear();app._select_dropdown_value('ARP_RANGE','4 OCT')
        assert_eq(fake.sent,[ARP_SYSEX['octaves_prefix']+bytes([4,0xF7])],'ARP range send')

        # Draw all major pages; this catches missing-key/runtime GUI regressions.
        for page in ('SYNTH','ARP + SEQUENCER','SONG','LIBRARY','SETTINGS'):
            app.page=page;app.redraw();app.update_idletasks()
    finally:
        app._closing=True
        try:app.destroy()
        except Exception:pass


def test_store_lock_static():
    app_text=(ROOT/'app.py').read_text(encoding='utf-8')
    if "0x28" not in app_text or 'store_locked' not in app_text or 'deploy_locked' not in app_text:
        raise AssertionError('STORE lock markers missing')
    # No numeric 0x28 SysEx constructor is allowed in runtime source.
    forbidden=('bytes((0xF0,0x00,0x21,0x1A,0x02,0x03,0x28',
               'bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x28')
    if any(x in app_text for x in forbidden):
        raise AssertionError('runtime contains a 0x28 SysEx sender')


def main():
    tests=[
        test_state_roundtrip_all_files,
        test_sequence_variants,
        test_matrix_slot59_cross_boundary_and_fade_lock,
        test_headless_app_paths,
        test_store_lock_static,
    ]
    for fn in tests:
        fn();print(f'PASS {fn.__name__}')
    print('PASS v1.58 regression suite')


if __name__=='__main__':
    main()
