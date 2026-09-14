from pathlib import Path
from types import SimpleNamespace as Event
import tempfile
from live_creator.ui.app import LiveCreator

def main():
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
        root=Path(d);p=root/'Bass.unosyp';p.write_bytes(b'original');a=LiveCreator(root/'state.json')
        try:
            a.update();a.set_root(root)
            a.source=p;a.drag_start=(0,0);a.drop(Event(x_root=a.timeline.winfo_rootx()+35,y_root=a.timeline.winfo_rooty()+45))
            assert a.model.length==1
            x1,x2,b,s,e=a.boxes[0];a.press(Event(x=x2-2));a.release(Event(x=x2+126));assert a.model.length==3
            x1,x2,b,s,e=a.boxes[0];a.press(Event(x=x1+15));a.release(Event(x=x1+143));assert a.model.blocks[0].preset is None
            a.name.set('Renamed');assert a.session.song.name=='Renamed'
            a.select(3);a.toggle_play();assert a.session.playing_pad==0
            a.select_pad(1);assert a.model.length==0 and a.session.playing_pad==0
            a.toggle_play();assert not a.session.active
            a.edit_delay('5 s');a.select_pad(0);a.edit_delay('5 s');a.toggle_play();assert a.session.pending_pad==0
            a.toggle_play();assert not a.session.active
            entry=next(w for w in a.work.winfo_children() if w.winfo_class()=='Entry')
            entry.focus_force();a.update();assert a.space(Event()) is None and not a.session.active
            a.grid_canvas.focus_force();a.update();assert a.space(Event())=='break' and a.session.active
            a.space(Event());assert not a.session.active
            p.unlink();a.render();assert a.library.label(str(p))=='PRESET NOT FOUND'
            for geometry in ['960x600','1200x750','1440x900']:
                a.geometry(geometry);a.update();assert a.left.winfo_width()==a.work.winfo_width()==260
                assert a.timeline.winfo_width()>a.winfo_width()-40 and len(a.pad_boxes)==64
                for n,x,y,size in a.pad_boxes:assert x>=0 and y>=0 and x+size<=a.grid_canvas.winfo_width() and y+size<=a.grid_canvas.winfo_height()
            a.flush();assert (root/'state.json').is_file()
            print('GUI PASS: drag, resize, EMPTY, 64-song switching, transport isolation, delay cancel, missing preset, geometry')
        finally:
            a.close()
        reopened=LiveCreator(root/'state.json')
        try:
            assert reopened.session.pads[0].name=='Renamed'
            assert reopened.session.pads[0].delay==5 and reopened.session.pads[0].timeline.length==5
            assert not reopened.session.active
            print('GUI PASS: Space text-focus guard, Space countdown cancel, state restart')
        finally:reopened.close()

if __name__=='__main__':main()
