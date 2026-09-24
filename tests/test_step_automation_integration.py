"""Check the application reader on variable-page and legacy containers."""
import json
import struct
import tempfile
import unittest
from pathlib import Path

from native_automation import read_automation
from uno_step_automation_decoder import MASTER_PAYLOAD
from uno_step_automation_decoder import decode as decode_step_automation
from uno_step_automation_decoder import pack7 as canonical_pack7
from uno_step_automation_decoder import roundtrip_binary
from uno_step_automation_decoder import pages as automation_pages
from uno_step_automation_decoder import write_resolved_values
from uno_step_automation_decoder import decode_native_value,encode_native_value
from unosyp_seq_decoder import decode_payload_note_steps
from unosyp_seq_decoder import parse_unosyp
import storage
from app import App
from data_model import Preset,Sequence
from native_automation import apply_decoded_to_sequence
from hardware_seq_0x29 import apply_to_sequence


def pack7(data):
    buffer = bits = 0
    out = bytearray()
    for byte in data:
        buffer |= byte << bits
        bits += 8
        while bits >= 7:
            out.append(buffer & 127)
            buffer >>= 7
            bits -= 7
    if bits:
        out.append(buffer & 127)
    return bytes(out)


def variable_file(payload=MASTER_PAYLOAD):
    result = bytearray(297)
    for index in range(4):
        extension = ((bytes((1, 16, 0, 0)) + payload) if index == 0 else payload)
        page = bytes(192) + pack7(extension)
        result += struct.pack('<I', len(page)) + page
    return bytes(result)


class AutomationIntegrationTest(unittest.TestCase):
    def test_pack7_is_exact_inverse(self):
        from uno_step_automation_decoder import unpack7
        samples=(b'',bytes(range(1,40)),bytes.fromhex('0102c8201f'),MASTER_PAYLOAD)
        for sample in samples:
            self.assertEqual(unpack7(canonical_pack7(sample)),sample)

    def test_confirmed_native_value_codecs(self):
        cases=(('ENV1',-21),('SPACING',64),('TUNE1',-12.0),
               ('LFO1',65.0),('CUTOFF1',101),('DRIVE',127),
               ('REVERB',100))
        for name,value in cases:
            raw=encode_native_value(name,value)
            self.assertEqual(decode_native_value(name,raw),value)
        with self.assertRaisesRegex(ValueError,'wave scale'):
            encode_native_value('WAVE1',2)
        for boundary in (0,512):
            with self.assertRaisesRegex(ValueError,'boundary'):
                encode_native_value('CUTOFF1',boundary)

    def test_drive_delay_order_variants_are_semantically_equal(self):
        fixtures={'c8':'DRIVE32_DELAY31_REVERSE','c0':'DRIVE32_DELAY31_CANONICAL'}
        decoded=[]
        for selection,profile in fixtures.items():
            payload=bytes.fromhex('201f')
            blob=bytearray(297)
            for page in range(4):
                logical=(bytes.fromhex('0102'+selection)+payload if page==0 else payload)
                body=bytes(192)+canonical_pack7(logical)
                blob+=struct.pack('<I',len(body))+body
            native=bytes(blob)
            item=decode_step_automation(native)
            self.assertEqual(item['profile'],profile)
            self.assertEqual([(x['name'],x['native_hex']) for x in item['parameters']],
                             [('DRIVE','20'),('DELAY','1f')])
            self.assertEqual(roundtrip_binary(native),native)
            decoded.append(item)
        self.assertEqual(decoded[0]['values_hex'],decoded[1]['values_hex'])
        self.assertNotEqual(decoded[0]['selection_hex'],decoded[1]['selection_hex'])

    def test_native_writer_changes_values_and_preserves_selection_and_cores(self):
        logical=[bytes.fromhex('0102c0201f'),bytes.fromhex('201f'),
                 bytes.fromhex('201f'),bytes.fromhex('201f')]
        blob=bytearray(297)
        for extension in logical:
            body=bytes(range(192))+canonical_pack7(extension)
            blob+=struct.pack('<I',len(body))+body
        source=bytes(blob)
        result=write_resolved_values(source,{(1,'DRIVE'):64,(1,'DELAY'):50})
        before=automation_pages(source);after=automation_pages(result)
        self.assertEqual(after[0]['extension'],bytes.fromhex('0102c04032'))
        self.assertEqual([p['extension'] for p in after[1:]],
                         [bytes.fromhex('4032')]*3)
        self.assertEqual(source[:297],result[:297])
        # Repacking must leave every page core byte-for-byte intact.
        def cores(data):
            offset=297;items=[]
            for _ in range(4):
                length=struct.unpack_from('<I',data,offset)[0]
                items.append(data[offset+4:offset+4+192]);offset+=4+length
            return items
        self.assertEqual(cores(source),cores(result))

    def test_native_writer_rejects_target_set_mutation(self):
        blob=bytearray(297)
        for extension in (bytes.fromhex('0102c0201f'),bytes.fromhex('201f'),
                          bytes.fromhex('201f'),bytes.fromhex('201f')):
            body=bytes(192)+canonical_pack7(extension)
            blob+=struct.pack('<I',len(body))+body
        source=bytes(blob)
        with self.assertRaisesRegex(ValueError,'cannot add unresolved'):
            write_resolved_values(source,{(1,'REVERB'):50})
        with self.assertRaisesRegex(ValueError,'cannot delete'):
            write_resolved_values(source,{(1,'DRIVE'):None})

    def test_save_as_keeps_binary_unosyp_and_writes_lane_values(self):
        blob=bytearray(297)
        for extension in (bytes.fromhex('0102c0201f'),bytes.fromhex('201f'),
                          bytes.fromhex('201f'),bytes.fromhex('201f')):
            body=bytes(192)+canonical_pack7(extension)
            blob+=struct.pack('<I',len(body))+body
        source=bytes(blob);sequence=Sequence();sequence.native_raw_hex=source.hex()
        apply_decoded_to_sequence(sequence,decode_step_automation(source))
        next(x for x in sequence.automation if x['parameter']=='DRIVE AMOUNT')['values'][0]=64
        next(x for x in sequence.automation if x['parameter']=='DELAY AMOUNT')['values'][0]=50
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'native.unosyp'
            storage.save_working_preset(Preset(sequence=sequence),target)
            saved=target.read_bytes()
        self.assertFalse(saved.lstrip().startswith(b'{'))
        self.assertEqual(automation_pages(saved)[0]['extension'].hex(),'0102c04032')

    def test_controlled_single_pair_gap_and_master7_profiles(self):
        root=Path(__file__).parents[2]
        fixtures={
            'upload/SG_WAVE1_fix.unosyp':('SINGLE_WAVE1',['WAVE1']),
            'upload/WAVE3_TUNE3.unosyp':('WAVE3_TUNE3',['WAVE3','TUNE3']),
            'upload/RES1_ENV1-fix.unosyp':('RES1_ENV1',['RES1','ENV1']),
            'upload/GAP_ENV1_ENV2_fix.unosyp':('GAP_ENV1_ENV2',['ENV1','ENV2']),
            'factory_corpus/MASTER_7.unosyp':(
                'MASTER_7',['WAVE1','TUNE1','WAVE2','TUNE2','WAVE3','TUNE3','NOISE']),
        }
        for relative,(profile,names) in fixtures.items():
            path=root/relative
            if not path.exists():self.skipTest(f'controlled fixture missing: {path}')
            decoded=decode_step_automation(path.read_bytes())
            self.assertEqual(decoded['profile'],profile)
            self.assertEqual([item['name'] for item in decoded['parameters']],names)
            self.assertTrue(decoded['pages_match'])

    def test_device_limit_is_eighteen_entries(self):
        from uno_step_automation_decoder import MAX_ENTRIES_PER_STEP
        self.assertEqual(MAX_ENTRIES_PER_STEP,18)

    def test_editor_json_sequence_is_auto_detected(self):
        steps=[{'notes':[],'note_velocities':[]} for _ in range(64)]
        steps[0]={'notes':[49],'note_velocities':[124],'gate':7,'control_raw':63}
        raw=json.dumps({'name':'JSON','sequence':{'length':62,'steps':steps,'automation':[]}}).encode()
        decoded=parse_unosyp(raw)
        self.assertEqual(decoded['format'],'editor-json')
        self.assertEqual(decoded['sequence_length'],62)
        self.assertEqual(decoded['active_steps'],[1])
        self.assertEqual(decoded['steps'][0]['voices'][0]['note_raw'],49)

    def test_variable_binary_pages_use_hardware_note_alignment(self):
        raw=bytearray([0xFF]*160);raw[0]=0;raw[1:10]=bytes((49,124,0,0xFF,0,0,0xFF,0,0))
        core=pack7(raw[1:]);core=core+bytes(192-len(core))
        state=bytearray(297);state[209]=16
        blob=state
        for _ in range(4):blob+=struct.pack('<I',len(core))+core
        decoded=parse_unosyp(bytes(blob))
        self.assertTrue(decoded['supported_sequence_variant'])
        self.assertEqual(decoded['steps'][0]['voices'][0]['note_raw'],49)

    def test_hardware_payload_keeps_fix13_note_alignment(self):
        raw = bytearray([0xFF] * 160)
        raw[0] = 0
        raw[1:10] = bytes((36, 100, 7, 0xFF, 0, 0, 0xFF, 0, 0))
        payload = pack7(raw[1:])
        payload = payload + bytes(192 - len(payload))
        steps = decode_payload_note_steps(payload, 0)
        self.assertEqual(steps[0]['voices'][0]['note_raw'], 36)
        self.assertEqual(steps[0]['voices'][0]['velocity'], 100)
        self.assertEqual(steps[0]['voices'][0]['extra_raw'], 7)
        self.assertFalse(steps[1]['active'])

    def test_known_profile_exposes_signed_values(self):
        decoded = read_automation(variable_file())
        self.assertEqual(decoded['status'], 'CAPTURE_PROFILE')
        self.assertEqual(decoded['entry_count'], 16)
        self.assertTrue(decoded['pages_match'])
        values = {item['parameter']: item['value'] for item in decoded['entries']}
        self.assertEqual((values['ENV1'], values['SPACING']), (-21, -32))

    def test_unknown_value_does_not_claim_parameter_names(self):
        changed = bytearray(MASTER_PAYLOAD)
        changed[0] = 12
        decoded = read_automation(variable_file(bytes(changed)))
        self.assertEqual(decoded['status'], 'PARTIAL')
        self.assertEqual(decoded['entry_count'], 16)
        self.assertEqual(decoded['entries'], [])

    def test_factory_multistep_cutoff1_is_visible(self):
        fixture=Path(__file__).parents[2]/'upload'/'FAKE 808(1).unosyp'
        if not fixture.exists():self.skipTest('factory fixture not present')
        decoded=read_automation(fixture.read_bytes())
        self.assertEqual(decoded['profile'],'FACTORY_MULTI_STEP_CUTOFF1')
        self.assertEqual([x['step'] for x in decoded['entries']],
                         [6,7,11,23,27,54,55,59])
        seq=storage.load_binary_unosyp_sequence(fixture)
        lane=next(x for x in seq.automation if x['parameter']=='CUTOFF 1')
        self.assertEqual([i+1 for i,v in enumerate(lane['values']) if v is not None],
                         [6,7,11,23,27,54,55,59])
        self.assertEqual(lane['values'][5],511)
        self.assertEqual(lane['values'][6],512)
        self.assertEqual(seq.native_automation['decoded_lane_points'],8)

    def test_editor_load_path_exposes_factory_cutoff1(self):
        fixture=Path(__file__).parents[2]/'upload'/'FAKE 808(1).unosyp'
        if not fixture.exists():self.skipTest('factory fixture not present')
        editor=App.__new__(App)
        editor.lib_selected=None;editor.preset_source='LOCAL';editor.automation_parameter='CUTOFF 1'
        editor._apply_params=lambda params:None
        editor._apply_state_cc=lambda cc,value:False
        editor._apply_extended_preset_fields=lambda fields:None
        editor._autofit_sequence_note_view=lambda:None
        editor.redraw=lambda:None
        self.assertTrue(App.load_local_preset(editor,fixture,preview=False))
        lane=next(x for x in editor.preset.sequence.automation if x['parameter']=='CUTOFF 1')
        self.assertEqual([i+1 for i,v in enumerate(lane['values']) if v is not None],
                         [6,7,11,23,27,54,55,59])

    def test_hardware_apply_exposes_factory_cutoff1(self):
        fixture=Path(__file__).parents[2]/'upload'/'FAKE 808(1).unosyp'
        if not fixture.exists():self.skipTest('factory fixture not present')
        raw=fixture.read_bytes();parse_unosyp(raw)
        pages={0:bytes(293)};offset=297
        for page_number in range(1,5):
            size=int.from_bytes(raw[offset:offset+4],'little');offset+=4
            pages[page_number]=raw[offset:offset+size];offset+=size
        sequence=Sequence()
        apply_to_sequence(sequence,pages)
        lane=next(x for x in sequence.automation if x['parameter']=='CUTOFF 1')
        self.assertEqual([i+1 for i,v in enumerate(lane['values']) if v is not None],
                         [6,7,11,23,27,54,55,59])
        self.assertEqual(lane['values'][5:7],[511,512])
        self.assertEqual(sequence.native_automation['decoded_lane_points'],8)


if __name__ == '__main__':
    unittest.main()
