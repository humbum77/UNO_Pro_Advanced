"""Regression checks for Library hardware selection and native STORE sources."""
import unittest
from unittest.mock import Mock
from tempfile import TemporaryDirectory
from pathlib import Path
import struct

from app import App
from local_store_source import build_current_buffer_load,build_local_unosyp,prepare_local_store


class StoreLibraryTest(unittest.TestCase):
    def test_local_panel_right_boundary_is_explicit(self):
        source=(Path(__file__).parents[1]/'app.py').read_text(encoding='utf-8')
        self.assertIn('self.line(left_x+left_w,panel_y,left_x+left_w,panel_y+panel_h,EDGE,1)',source)

    def test_noise_fader_is_present(self):
        source=(Path(__file__).parents[1]/'app.py').read_text(encoding='utf-8')
        self.assertIn("self.slider(noise_x,fy,fh,'NOISE','NOISE_LEVEL',0,127,False,vertical=True,show_label=False)",source)

    def test_library_split_is_three_local_columns_and_wider_right_panel(self):
        app = object.__new__(App)
        app.layout_w = 1600
        app._lib_tooltip = None
        app.rect = Mock()
        app.line = Mock()
        app.text = Mock()
        app.button = Mock()
        app._draw_local_panel = Mock()
        app._draw_right_panel = Mock()
        App.draw_library(app)
        app._draw_local_panel.assert_called_once_with(24,105,890,800)
        app._draw_right_panel.assert_called_once_with(942,105,634,800)

    def test_tag_circles_match_star_scale(self):
        app = object.__new__(App)
        app.lib_star_filter = False
        app.lib_color_filters = set()
        app.rect = Mock()
        app.text = Mock()
        app.hitbox = Mock()
        app._draw_aa_circle = Mock()
        App._draw_tag_tools(app,0,0)
        self.assertEqual([call.args[2] for call in app._draw_aa_circle.call_args_list],[20]*7)

    def test_library_toolbar_has_get_send_and_no_store(self):
        app = object.__new__(App)
        app.lib_right_mode = 'UNO'
        app._catalog_active=False;app._catalog_seen=set()
        app._tool_icon = Mock()
        app.button = Mock()
        app.rect = Mock()
        app._draw_uno_slots = Mock()
        App._draw_right_panel(app, 0, 0, 500, 780)
        labels = [call.args[2] for call in app._tool_icon.call_args_list]
        self.assertEqual(labels, ['Uno'])
        self.assertEqual([call.args[4] for call in app.button.call_args_list],['GET','SEND'])

    def test_dragged_file_supplies_store_state_and_sequence(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / 'DRAGGED.unosyp'
            body = bytearray(297)
            body[:4] = bytes((0x25, 0x01, 0, 0))
            originals = {}
            for page in range(1, 5):
                payload = bytes([page]) * 192
                originals[page] = payload
                body.extend(struct.pack('<I', len(payload)))
                body.extend(payload)
            source.write_bytes(body)
            state, pages, name = prepare_local_store(source)
            self.assertEqual((len(state), pages, name), (309, originals, 'DRAGGED'))
            rebuilt=build_local_unosyp(state,{0:bytes(body[4:297]),**pages})
            self.assertEqual(rebuilt,bytes(body))

            app = object.__new__(App)
            app._store_tx = app._store_pending = None
            app.midi = Mock(out=object())
            app._confirm = Mock(return_value=True)
            app._notify = Mock()
            app._execute_store_from_state = Mock(return_value=True)
            app._cancel_hardware_sequence_read = Mock()
            app.after_cancel = Mock()
            for attr in ('_hw_refresh_job','_hw_name_job','_hw_seq_job','_catalog_job','_catalog_timeout_job'):
                setattr(app, attr, None)
            self.assertTrue(App._store_local_file_to_hardware(app,source,166))
            app._execute_store_from_state.assert_called_once_with(state,166,'DRAGGED',originals)
            app.midi.bank_program.assert_not_called()

    def test_missing_binary_source_is_rejected_before_store(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / 'LOCAL.unosyp'
            source.write_text('{"sequence": {}}')
            app = object.__new__(App)
            app._store_tx = app._store_pending = None
            app._notify = Mock()
            app._execute_store_from_state = Mock()
            self.assertFalse(App._store_local_file_to_hardware(app,source,166))
            app._execute_store_from_state.assert_not_called()

    def test_store_toolbar_is_synth_only(self):
        source=(Path(__file__).parents[1]/'app.py').read_text(encoding='utf-8')
        self.assertIn("if self.page=='SYNTH':self.button(right+194,8,82,34,'STORE'",source)

    def test_current_buffer_load_is_built_from_selected_binary_file(self):
        with TemporaryDirectory() as tmp:
            source=Path(tmp)/'SELECTED.unosyp';body=bytearray(0x129)
            body[:4]=bytes((0x25,1,0,0));body[4:]=bytes((i%128 for i in range(0x125)));source.write_bytes(body)
            message=build_current_buffer_load(source)
            self.assertEqual(message[:9],bytes((0xF0,0,0x21,0x1A,2,3,0x36,0,0x60)))
            self.assertEqual(message[9:-1],bytes(body[4:0x129]));self.assertEqual(message[-1],0xF7)

    def test_move_left_receives_selected_hardware_slot_to_selected_folder(self):
        with TemporaryDirectory() as tmp:
            app = object.__new__(App)
            app.lib_right_mode = 'UNO';app.lib_hw_selected = 53;app.lib_panel_folder = [Path(tmp),None]
            app._receive_hardware_to_folder = Mock(return_value=True)
            self.assertTrue(App._library_move_left(app))
            app._receive_hardware_to_folder.assert_called_once_with(53,Path(tmp))

    def test_ctrl_and_shift_select_local_presets(self):
        app=object.__new__(App);files=[Path(f'/tmp/{n}.unosyp') for n in range(6)]
        app.lib_panel_folder=[Path('/tmp'),None];app.lib_selected=None;app.lib_selected_many=set();app._lib_local_anchor=None
        app._filtered_files=Mock(return_value=files)
        App._select_local_library_item(app,files[1],0)
        App._select_local_library_item(app,files[4],0x0001)
        self.assertEqual(app.lib_selected_many,set(files[1:5]))
        App._select_local_library_item(app,files[0],0x0004)
        self.assertEqual(app.lib_selected_many,set(files[1:5])|{files[0]})
        App._select_local_library_item(app,files[2],0x0004)
        self.assertNotIn(files[2],app.lib_selected_many)

    def test_ctrl_and_shift_select_hardware_slots(self):
        app=object.__new__(App);app.lib_hw_selected=1;app.lib_hw_selected_many=set();app._lib_hw_anchor=None
        App._select_hardware_library_item(app,3,0)
        App._select_hardware_library_item(app,6,0x0001)
        self.assertEqual(app.lib_hw_selected_many,{3,4,5,6})
        App._select_hardware_library_item(app,9,0x0004)
        self.assertEqual(app.lib_hw_selected_many,{3,4,5,6,9})

    def test_move_right_maps_multiple_files_from_one_start_slot(self):
        app=object.__new__(App);files=[Path(f'/tmp/{n}.unosyp') for n in range(3)]
        app.lib_panel_folder=[Path('/tmp'),None];app.lib_selected=files[0];app.lib_selected_many=set(files)
        app.lib_right_mode='UNO';app.lib_hw_selected=100;app.lib_hw_selected_many={100}
        app._filtered_files=Mock(return_value=files);app._stage_local_files=Mock(return_value=True);app._notify=Mock()
        self.assertTrue(App._library_move_right(app))
        app._stage_local_files.assert_called_once_with(files,[100,101,102])

    def test_move_left_queues_multiple_hardware_slots(self):
        app=object.__new__(App);app.lib_right_mode='UNO';app.lib_hw_selected=3;app.lib_hw_selected_many={3,5,8}
        app.lib_panel_folder=[Path('/tmp'),None];app._receive_pending=None;app._receive_batch_queue=[];app._receive_batch_next=Mock()
        self.assertTrue(App._library_move_left(app))
        self.assertEqual(app._receive_batch_queue,[(3,Path('/tmp')),(5,Path('/tmp')),(8,Path('/tmp'))])
        app._receive_batch_next.assert_called_once()

    def test_last_hardware_column_contains_slot_256(self):
        app = object.__new__(App)
        app.lib_hscroll = [0,10**9]
        app.lib_hw_selected = 1
        app.hardware_selected = 1
        app.hardware_names = {}
        app.rect = Mock();app.text = Mock();app.line = Mock();app.hitbox = Mock()
        App._draw_uno_slots(app,0,0,634,758)
        visible_slots=[call.args[5] for call in app.hitbox.call_args_list if call.args[4]=='hwslot']
        self.assertIn(256,visible_slots)
        hardware_boxes=[call.args[:4] for call in app.hitbox.call_args_list if call.args[4]=='hwslot']
        self.assertTrue(all(x>=6 and x+w<=628 for x,y,w,h in hardware_boxes))

    def test_bank_queue_runs_consecutive_prepared_presets(self):
        app = object.__new__(App)
        app._store_tx = None
        app._store_batch_queue = [('state1','pages1','one',101),('state2','pages2','two',102)]
        app._store_batch_total = 2;app._store_batch_done = 0
        app._execute_store_from_state = Mock(return_value=True)
        App._store_batch_next(app)
        app._execute_store_from_state.assert_called_once_with('state1',101,'one','pages1')
        self.assertEqual(app._store_batch_queue,[('state2','pages2','two',102)])


if __name__ == '__main__':
    unittest.main()
