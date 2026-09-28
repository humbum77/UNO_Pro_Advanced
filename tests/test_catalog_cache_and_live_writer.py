import json,tempfile,unittest
from pathlib import Path

from live_creator.core import state
from live_creator.core.session import Session
from live_creator.devices.uno.catalog_cache import load_cache,load_names,save_cache,save_names
from live_creator.devices.uno.timing import decode_hardware_sequence_length
from live_creator.ui.app import LiveCreator


class CatalogCacheAndHardwareClipsTest(unittest.TestCase):
    def test_catalog_cache_roundtrip_and_slot_filter(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'catalog.json'
            save_names({1:'INIT',174:'LAST FACTORY',256:'USER'},path)
            self.assertEqual(load_names(path),{1:'INIT',174:'LAST FACTORY',256:'USER'})
            data=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(data['version'],2)

    def test_catalog_snapshot_records_verification_without_losing_cached_names(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'catalog.json'
            save_cache({1:'INIT',2:'BASS',256:'USER'},path,{1,2},{3},'start','finish')
            snapshot=load_cache(path)
            self.assertEqual(snapshot['names'][256],'USER')
            self.assertEqual(snapshot['verified_slots'],[1,2])
            self.assertEqual(snapshot['missing_slots'],[3])
            save_names({1:'INIT 2',2:'BASS',256:'USER'},path)
            updated=load_cache(path)
            self.assertEqual(updated['names'][1],'INIT 2')
            self.assertEqual(updated['verified_slots'],[1,2])
            self.assertEqual(updated['last_scan_completed'],'finish')

    def test_catalog_is_pipelined_and_hardware_clips_keep_pages(self):
        root=Path(__file__).resolve().parents[1]
        main=(root/'app.py').read_text(encoding='utf-8')
        live=(root/'live_creator/ui/app.py').read_text(encoding='utf-8')
        self.assertIn("self._catalog_job=self.after(5 if self._catalog_retry==0 else 20",main)
        self.assertNotIn("self.after(350,self._start_hardware_catalog)",live)
        self.assertIn("if self._catalog_retry<3",main)
        self.assertIn("if self._catalog_retry<3",live)
        self.assertIn("'hardware_pages':{str(page):bytes(pages[page]).hex()",live)
        self.assertIn("self._restore_hardware_snapshots()",live)
        self.assertNotIn("Save current editor preset here",live)

    def test_block_parameters_survive_state_roundtrip(self):
        session=Session()
        parameters={'hardware_slot':53,'hardware_name':'FAKE 808',
                    'hardware_pages':{str(page):('00'*293 if page==0 else '00'*192) for page in range(5)}}
        session.song.timeline.insert(0,'hardware://053/FAKE 808',parameters=parameters)
        restored=state.decode(state.encode(session))
        self.assertEqual(restored.song.timeline.blocks[0].parameters,parameters)

    def test_factory_clip_snapshot_restores_without_local_file(self):
        page0=bytearray(293);page0[203]=127;page0[204]=0  # 16 steps
        pages={str(page):(bytes(page0) if page==0 else bytes(192)).hex() for page in range(5)}
        session=Session();session.song.timeline.insert(
            0,'hardware://053/FAKE 808',parameters={
                'hardware_slot':53,'hardware_name':'FAKE 808','hardware_pages':pages})
        live=LiveCreator.__new__(LiveCreator);live.session=state.decode(state.encode(session))
        live.hardware_pages={};live.hardware_sequence_status={};live.hardware_names={}
        live._restore_hardware_snapshots()
        self.assertEqual(live.hardware_names[53],'FAKE 808')
        self.assertEqual(live.hardware_pages[53][0],bytes(page0))
        self.assertEqual(live._sequence_beats_for('hardware://053/FAKE 808'),4.0)
        self.assertEqual(live._snapshot_restore_slots,set())
        self.assertEqual(decode_hardware_sequence_length(bytes(page0)),16)


if __name__=='__main__':unittest.main()
