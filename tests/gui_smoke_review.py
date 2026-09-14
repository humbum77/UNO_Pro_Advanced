from pathlib import Path
from types import SimpleNamespace as E
import tempfile,tkinter as tk,time
from live_creator.ui.app import LiveCreator
from live_creator.ui.popups import ColorPalette,ObjectMenu
from review_preview import populate

def main():
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
        root=Path(folder);a=LiveCreator(root/'state.json')
        try:
            populate(a,root);a.update();a.select(21);a.loop_selection();a.select(1)
            a.toggle_play();assert a.session.playing_pad==0
            a.select_pad(1);assert a.session.playing_pad==0
            a.select_pad(0);a.toggle_play();assert not a.session.active
            a.model.loop_range=None;a.select(21);a.edit_action('copy')
            a.select_pad(10);a.edit_context='block';a.edit_action('paste');assert not a.model.markers
            assert len(a.model.blocks)==1 and a.model.blocks[0].color=='#d0a571'
            a.select_pad(0);g=a.geometry_slots();x,y=g.point(21)
            event=E(x=x+g.pitch/2,y=y+15,x_root=a.timeline.winfo_rootx()+x,y_root=a.timeline.winfo_rooty()+y)
            a.block_menu(event);assert isinstance(a.popup,ObjectMenu)
            assert [item[0] for item in a.popup.items if item]==['Set Marker','Delete Marker','Color...','Loop','Cut','Copy','Paste','Delete']
            a.popup.destroy();a.choose_color('block',100,100);assert isinstance(a.popup,ColorPalette);a.popup.choose(E(x=9,y=9))
            assert a.selected().color is not None
            a.select_pad(1);pad=a.pad_boxes[1];a.song_menu(E(x=pad[1]+10,y=pad[2]+10,x_root=100,y_root=100))
            assert [item[0] for item in a.popup.items if item]==['Color...','Cut','Copy','Paste','Delete'];a.popup.destroy()
            a.choose_color('song',100,100);a.popup.choose(E(x=33,y=35));a.update()
            assert a.name_entry.cget('background')==a.session.song.color and a.name_entry.cget('justify')=='center'
            a.select_pad(0);a.select(21);a.edit_action('cut');assert 'Marker conflict' in a.status.get()
            a.update();assert a.error_label.winfo_ismapped()
            assert a.model.length==40 and a.model.markers[21]=='CHORUS'
            a.model.markers.pop(36);a.edit_action('cut');assert a.model.markers[21]=='CHORUS'
            a.edit_action('paste');assert len(a.model.blocks)==4
            for geometry in ('960x600','1200x750','1440x900'):
                a.geometry(geometry);a.update();assert len(a.timeline.find_withtag('slot-number'))==64
                assert a.left.winfo_width()==a.work.winfo_width()==260
                for n,x,y,size in a.pad_boxes:assert x+size<=a.grid_canvas.winfo_width() and y+size<=a.grid_canvas.winfo_height()
            a.name_entry.focus_force();a.update();assert a.edit_action('delete',E()) is None
            a.timeline.focus_force();a.update();a.select(1);a.clipboard.kind=None
            a.timeline.event_generate('<KeyPress>',keycode=67,state=4);a.update();assert a.clipboard.kind=='blocks'
            a.select_pad(10);a.grid_canvas.focus_force();a.update()
            a.grid_canvas.event_generate('<KeyPress>',keycode=67,state=4);a.update();assert a.clipboard.kind=='song'
            a.grid_canvas.event_generate('<KeyPress>',keycode=88,state=4);a.update();assert not a.model.length
            a.grid_canvas.event_generate('<KeyPress>',keycode=86,state=4);a.update();assert a.model.length==15
            a.grid_canvas.event_generate('<Delete>');a.update();assert not a.model.length
            assert all(p.is_file() for p in (root/'fixtures').glob('*.unosyp'))
            a.flush();assert not any(p.suffix!='.unosyp' for p in (root/'fixtures').iterdir())
            print('GUI REVIEW PASS: menus, palette, markers, clipboard, isolation, NAME, text guards, 32+32, square pads, no service files in presets')
        finally:a.close()

if __name__=='__main__':main()
