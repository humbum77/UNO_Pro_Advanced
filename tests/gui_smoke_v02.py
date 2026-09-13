"""Native Tk event-handler smoke test; no hardware connection."""
from pathlib import Path
import tempfile
from types import SimpleNamespace as Event
from live_creator.ui.app import LiveCreator

def main():
    app=LiveCreator()
    try:
        app.update()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            p=Path(folder)/'Bass.unosyp';p.write_bytes(b'original raw preset')
            app.set_root(folder)
            assert len(app.browser_rows)==1
            def drop(x):
                app.source=p;app.drag_start=(0,0)
                app.drop(Event(x_root=app.timeline.winfo_rootx()+x,y_root=app.timeline.winfo_rooty()+65))
            drop(40);assert app.model.length==1
            x1,x2,b,s,e=app.boxes[0]
            app.press(Event(x=x2-3));app.release(Event(x=x2-3+128));assert app.model.length==3
            drop(app.boxes[-1][1]+25);assert len(app.model.blocks)==2
            x1,x2,b,s,e=app.boxes[1]
            app.press(Event(x=x1+20));app.release(Event(x=x1+148));assert app.model.blocks[1].preset is None
            app.select(6);assert app.selected().preset is not None
            n,x,y,size=app.pad_boxes[0];app.pad_click(Event(x=x+size/2,y=y+size/2));assert app.model.selected_step==1
            n,x,y,size=app.pad_boxes[-1];app.pad_click(Event(x=x+size/2,y=y+size/2));assert app.model.selected_step==1
            drop(50);assert app.model.blocks[0].length==3
            app.model.set_playhead(2);app.render();assert app.model.selected_step==1
            for geometry in ['960x600','1200x750','1440x900']:
                app.geometry(geometry);app.update();assert len(app.pad_boxes)==64
                assert app.left.winfo_width()==app.work.winfo_width()==260
                assert app.timeline.winfo_width()>app.winfo_width()-40
                for n,x,y,size in app.pad_boxes:
                    assert x>=0 and y>=0 and x+size<=app.grid_canvas.winfo_width() and y+size<=app.grid_canvas.winfo_height()
            app.select(1);app.select(6,True);app.loop_selection();assert app.model.loop_range==(1,6)
            app.toggle_play();assert app.model.playhead==6;app.select(1);assert app.model.playhead==6
            app.tick();assert app.model.playhead==1;app.stop()
            app.browser_mode.choose('HARDWARE PRESETS');assert not app.browser_rows
            app.set_mode('LIVE');assert app.mode=='LIVE'
            print('GUI PASS: drop/replace, resize, move/EMPTY, selection, disabled pads, playhead, 3 window sizes')
    finally:app.destroy()

if __name__=='__main__':main()
