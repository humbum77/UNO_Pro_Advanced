from pathlib import Path
from hardware_seq_0x29 import parse_0x29_response,decode_pages
cap=Path("/mnt/data/to_lib_preset001.txt").read_text(errors="replace")
pages={}
for line in cap.splitlines():
    c=line.split("\t")
    if len(c)<6 or c[2]!="UNO→EDITOR" or c[3]!="SysEx":continue
    try:d=bytes(int(x,16) for x in c[5].split())
    except ValueError:continue
    p=parse_0x29_response(d)
    if p:pages[p[0]]=p[1]
assert {k:len(v) for k,v in pages.items()}=={0:293,1:192,2:192,3:192,4:192}
info=decode_pages(pages)
assert len(info["steps"])==64
assert info["unknown_control_steps"]==[1,17,33,49]
assert info["steps"][0]["notes"]==[0x2E]
assert info["steps"][2]["notes"]==[0x3D]
print("PASS: 0x29 pages/64 steps decoded")
