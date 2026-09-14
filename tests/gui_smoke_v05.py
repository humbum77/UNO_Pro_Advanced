from pathlib import Path
from types import SimpleNamespace as E
import tempfile
import tkinter as tk
from unittest.mock import patch
from live_creator.ui.app import LiveCreator,COLORS

def main():
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
        root=Path(folder);preset=root/'Long preset name.unosyp';preset.write_bytes(b'untouched')
        a=LiveCreator(root/'state.json')
        try:
            a.update();a.set_root(root)
            assert len(a.tree.find_withtag('preset-number'))==1
            assert a.grid_canvas.itemcget(a.grid_canvas.find_withtag('pad-label-0')[0],'text')=='01'
            g=a.geometry_slots();x,y=g.point(30)
            event=E(x_root=a.timeline.winfo_rootx()+x+g.pitch/2,y_root=a.timeline.winfo_rooty()+y+12)
            a.source=preset;a.drag_start=(0,0);a.tree_motion(event)
            assert a.preview[0][0]=='INSERT' and a.timeline.find_withtag('preview')
            assert a.ghost.winfo_manager()=='place'
            a.drop(event);assert a.model.length==30 and a.model.blocks[0].length==29
            block=a.model.blocks[1];a.model.resize(block.id,6);a.render()
            segments=[b for b in a.boxes if b[4].id==block.id];assert len(segments)==2
            for x,y,x2,y2,b,s,e,start,end in segments:assert abs((x2-x)-(e-s+1)*g.pitch)<.001
            a.press(E(x=segments[1][0]+g.pitch/2,y=segments[1][1]+15,state=0));a.release(E(x=segments[1][0]+g.pitch/2,y=segments[1][1]+15))
            assert a.model.selection=={block.id}
            last=segments[1];a.press(E(x=last[2]-1,y=last[1]+15,state=0));a.release(E(x=last[2]-1+g.pitch,y=last[1]+15))
            assert a.model.blocks[1].length==7
            last=[b for b in a.boxes if b[4].id==block.id][-1]
            a.press(E(x=last[2]-1,y=last[1]+15,state=0));a.release(E(x=last[2]-1-g.pitch,y=last[1]+15))
            assert a.model.blocks[1].length==6
            first=[b for b in a.boxes if b[4].id==block.id][0]
            a.press(E(x=first[0]+g.pitch/2,y=first[1]+15,state=0));a.release(E(x=first[0]+g.pitch*1.5,y=first[1]+15))
            assert a.model.blocks[0].length==30
            first=[b for b in a.boxes if b[4].id==block.id][0]
            a.press(E(x=first[0]+g.pitch/2,y=first[1]+15,state=0));a.release(E(x=first[0]-g.pitch/2,y=first[1]+15))
            assert a.model.blocks[0].length==29
            a.name.set('My long song with several words');a.choose_color(E(x=33));assert a.session.song.color==COLORS[1]
            a.toggle_play();assert a.play_button.text=='STOP'
            a.session.update(a.session.next_tick+100);a.render();assert a.play_button.text=='STOP'
            a.select_pad(1);assert a.session.playing_pad==0 and a.model.length==0
            a.toggle_play();assert not a.session.active
            a.select_pad(0);a.edit_delay('5 s')
            entry=next(w for w in a.work.winfo_children() if isinstance(w,tk.Entry))
            entry.focus_force();a.update();assert a.space(E()) is None
            a.timeline.focus_force();a.update();a.space(E());assert a.session.pending_pad==0
            a.space(E());assert not a.session.active
            a.select(30);a.loop_selection();assert a.model.loop_range==(30,35)
            a.render();x,y=a.geometry_slots().point(30)
            assert a.target(x+g.pitch/2,y+12)[0]=='REPLACE'
            assert a.target(x+.05*g.pitch,y+12)[0]=='INSERT'
            a.delete_blocks();assert a.model.length==29 and not a.model.selection
            a.model.select(1);a.delete_blocks();assert not a.model.length
            a.model.insert(0,str(preset),1);a.render()
            x,y=a.geometry_slots().point(1)
            with patch.object(tk.Menu,'tk_popup',lambda menu,*args:menu.invoke(0)):
                a.block_menu(E(x=x+g.pitch/2,y=y+15,x_root=0,y_root=0))
            assert a.model.length==0
            a.model.insert(0,str(preset),1);a.render()
            for geometry in ('960x600','1200x750','1440x900'):
                a.geometry(geometry);a.update()
                assert a.left.winfo_width()==a.work.winfo_width()==260
                assert len(a.timeline.find_withtag('slot-number'))==64
                assert len(a.timeline.find_withtag('slot-grid'))==66
                assert not a.timeline.find_withtag('playhead')
                for n,x,y,size in a.pad_boxes:assert x>=0 and y>=0 and x+size<=a.grid_canvas.winfo_width() and y+size<=a.grid_canvas.winfo_height()
            assert a.play_button.winfo_y()<a.delay.master.winfo_y()<entry.winfo_y()
            assert not hasattr(a,'context') and not a.error_label.winfo_ismapped()
            a.flush();assert preset.read_bytes()==b'untouched'
        finally:a.close()
        reopened=LiveCreator(root/'state.json')
        try:
            reopened.update();assert reopened.session.song.color==COLORS[1]
            assert reopened.session.song.name=='My long song with several words'
            assert not reopened.session.active
            print('GUI PASS: 32+32, wrapped block, EMPTY geometry, preview INSERT/REPLACE, numbering, delete, transport, Space, layout, color/state restart')
        finally:reopened.close()

if __name__=='__main__':main()
