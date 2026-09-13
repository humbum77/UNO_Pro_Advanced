import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pathlib import Path
import ast
from protocol_map import preset_page_read, COMMANDS
src=Path('app.py').read_text(encoding='utf-8')
ast.parse(src)
assert "'100%':(1200,675)" in src and "'125%':(1440,810)" in src and "'150%':(1600,900)" in src
assert "'FULLSCREEN'" in src and "'50%'" not in src[src.index('def _apply_ui_scale'):src.index('def _mod_routes_for_dest')]
assert "self.text(520,80,self._sequence_source_label()" not in src
assert "self._seq_fill_flash" in src
assert "fine[s]=[None]*4" in src
assert "left_w=900;gap=28" in src and "right_w=612" in src
assert "col_w=210 if idx==0 else 290" in src
assert "and e.keysym=='Return'" in src
assert "self.lib_selected=files[i];self.redraw()" in src
assert preset_page_read(1,0).hex(' ') == 'f0 00 21 1a 02 03 29 00 00 00 f7'
assert preset_page_read(2,0).hex(' ') == 'f0 00 21 1a 02 03 29 00 01 00 f7'
assert preset_page_read(129,4).hex(' ') == 'f0 00 21 1a 02 03 29 01 00 04 f7'
assert 'LOCKED' in COMMANDS[0x28]
print('PASS v1.63 static regression')
