import importlib.util
import pathlib
import queue
import threading
import time
import unittest
from unittest.mock import Mock, patch

path = pathlib.Path(__file__).resolve().parents[1] / 'uno_midi_monitor_winapi.py'
spec = importlib.util.spec_from_file_location('monitor', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class CCTests(unittest.TestCase):
    def test_exact_list(self):
        expected = {2,3,4,6,8,10,11,27,33,34,42,43,52,94,99,106,121} | set(range(83,90)) | set(range(115,120)) | set(range(124,128))
        self.assertEqual(set(m.TEST_CCS), expected)
        self.assertEqual(len(m.TEST_CCS), 33)

    def test_packets(self):
        for cc in m.TEST_CCS:
            for channel in (1,16):
                for value in (0,64,127):
                    self.assertEqual(m.cc_packet(channel,cc,value), bytes((0xB0+channel-1,cc,value)))
        for args in ((0,2,0),(17,2,0),(1,82,0),(1,2,-1),(1,2,128)):
            with self.assertRaises(ValueError): m.cc_packet(*args)

    def test_manual_queue_and_filters(self):
        a = object.__new__(m.App)
        a.running=True; a.stopping=False; a.uno_out=Mock(); a.status=Mock()
        a.forward_queue=queue.Queue(); a.test_channel=Mock(); a.test_cc=Mock(); a.test_value=Mock()
        a.test_channel.get.return_value='1'; a.test_cc.get.return_value='2'; a.test_value.get.return_value='45'
        a.send_test_cc()
        self.assertEqual(a.forward_queue.get_nowait(), ('TEST→UNO',b'\xb0\x02\x2d'))
        self.assertTrue(a.forward_queue.empty())
        a.send_test_cc(127)
        self.assertEqual(a.forward_queue.get_nowait(), ('TEST→UNO',b'\xb0\x02\x7f'))
        a.capture_clock=False; a.capture_active_sense=False; a.capture_channel=None
        self.assertFalse(a._should_capture(b'\xf8',False))
        self.assertFalse(a._should_capture(b'\xfe',False))
        self.assertTrue(a._should_capture(b'\xfa',False))
        a.capture_clock=True
        self.assertTrue(a._should_capture(b'\xf8',False))

    def test_worker_routes_once(self):
        a=object.__new__(m.App); a.forward_stop=threading.Event(); a.stopping=False
        a.forward_queue=queue.Queue(); a.error_queue=queue.Queue(); a.uno_out=Mock(); a.editor_out=Mock()
        a._record_test_send=Mock(side_effect=lambda data: a.forward_stop.set())
        a.forward_queue.put(('TEST→UNO',b'\xb0\x02\x40'))
        a._forward_worker()
        a.uno_out.send.assert_called_once_with(b'\xb0\x02\x40')
        a.editor_out.send.assert_not_called()
        a._record_test_send.assert_called_once()

if __name__=='__main__': unittest.main(verbosity=2)
