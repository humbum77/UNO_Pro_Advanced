import tempfile,unittest
from pathlib import Path

from live_creator.devices.uno.hardware_bank import load_bank,local_entry,reset_from_catalog,save_bank


class HardwareBankTest(unittest.TestCase):
    def test_catalog_reset_and_staging_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bank.json';preset=Path(folder)/'BASS.unosyp'
            bank=reset_from_catalog({1:'ONE',128:'LAST',256:'USER'},path)
            self.assertEqual(bank[128]['name'],'LAST')
            self.assertEqual(bank[128]['source_slot'],128)
            bank[9]=local_entry(preset);save_bank(bank,path)
            restored=load_bank({},path)
            self.assertEqual(restored[9]['kind'],'local')
            self.assertEqual(restored[9]['path'],str(preset))
            self.assertTrue(restored[9]['dirty'])

    def test_factory_slots_are_not_special_or_immutable(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bank.json';bank=reset_from_catalog({1:'CUSTOM'},path)
            bank[1]=local_entry(Path(folder)/'replacement.unosyp');save_bank(bank,path)
            self.assertEqual(load_bank({},path)[1]['kind'],'local')


if __name__=='__main__':unittest.main()
