"""Read-only validation against supplied captures, not a live hardware test."""
import hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from native_automation import read_automation,sequence_length
from live_creator.devices.uno.timing import sequence_beats
import storage

def main(folder):
 root=Path(folder)
 for name,size in [('REF2',0),('AUTO_L4',2),('AUTO_L5',2),('AUTO_L6',4),('AUTO_L',28),('AUTO_L2',34)]:
  p=root/(name+'.unosyp');data=p.read_bytes();info=read_automation(data)
  assert info['payload_length']==size and info['entry_count']==size//2
  expected={'AUTO_L4':'2901','AUTO_L5':'580e','AUTO_L6':'580e08c3'}.get(name)
  if expected:assert info['payload_hex']==expected
  seq=storage.load_binary_unosyp_sequence(p);assert seq.native_raw_hex==data.hex() and seq.native_automation==info
  assert p.read_bytes()==data
  print(name,size,size//2,hashlib.sha256(data).hexdigest())
 count=0
 for p in root.glob('LEN-*.unosyp'):
  n=int(p.stem.split('-')[1]);data=p.read_bytes();assert sequence_length(data)==n and sequence_beats(p)==n/4
  assert storage.load_binary_unosyp_sequence(p).length==n
  count+=1
 assert count==12
 print('CAPTURE SOFTWARE PASS: 6 automation containers + 12 sequence lengths. No hardware sends.')

if __name__=='__main__':main(sys.argv[1])
