"""Isolated visual review fixture. Not a build and not user preset data."""
from pathlib import Path
import tempfile,json,sys,time
from types import SimpleNamespace as E
from live_creator.ui.app import LiveCreator

def populate(app,root):
    library=root/'fixtures';library.mkdir(exist_ok=True)
    for index,(name,length,color) in enumerate([('Dark bass',8,'#283852'),('Warm keys',12,'#7560a1'),('Bright lead',15,'#d0a571'),('Outro',5,'#427569')]):
        preset=library/(name+'.unosyp')
        preset.write_text(json.dumps({'sequence':{'length':16,'length_confirmed':True,'resolution':'1/4'}}))
        id=app.model.insert(index,str(preset),length);app.model.set_color({id},color)
    app.model.set_marker(1,'INTRO');app.model.set_marker(9,'VERSE');app.model.set_marker(21,'CHORUS');app.model.set_marker(36,'OUTRO')
    app.session.song.name='Northern Lights';app.session.song.color='#496879'
    app.clipboard.copy_song(app.session.song)
    for pad,color in [(1,'#283852'),(2,'#7560a1'),(3,'#d0a571')]:
        app.session.pads[pad]=app.clipboard.paste_song();app.session.pads[pad].name=['','Dark River','Quiet Hours','Golden Sky'][pad];app.session.pads[pad].color=color
    app.clipboard.kind=None;app.clipboard.data=None
    app.set_root(library);app.sync_editor();app.render()

def main():
    with tempfile.TemporaryDirectory(prefix='review-',dir=Path(__file__).parent) as folder:
        root=Path(folder);app=LiveCreator(root/'state.json');populate(app,root)
        scene=sys.argv[1] if len(sys.argv)>1 else 'main'
        app.title('Live Creator — isolated review' if scene=='main' else 'Live Creator — review '+scene)
        app.update()
        if scene=='move' or scene.startswith('resize'):
            box=app.boxes[1];x=box[2]-1 if scene.startswith('resize') else box[0]+20;y=box[1]+15
            app.press(E(x=x,y=y,state=0));app.motion(E(x=x+app.geometry_slots().pitch*2,y=y))
        elif scene.startswith('pulse-'):
            index={'pulse-dark':1,'pulse-medium':2,'pulse-bright':3}[scene]
            app.select_pad(index);app.select({1:1,2:9,3:21}[index]);app.toggle_play()
        elif scene.startswith('marker-conflict'):
            app.select(1);app.perform(app.model.delete_selected)
        app.mainloop()

if __name__=='__main__':main()
