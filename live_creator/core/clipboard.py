"""Process-local clipboard. No filesystem operations, no block markers."""
from copy import deepcopy
from dataclasses import replace
from uuid import uuid4

class Clipboard:
    kind=None
    data=None
    def copy_blocks(self,song):
        blocks=[replace(b,color=b.color or song.colors.get(b.preset)) for b in song.timeline.blocks if b.id in song.timeline.selection]
        if blocks:self.kind='blocks';self.data=deepcopy(blocks)
    def paste_blocks(self,song,index):
        if self.kind!='blocks':return
        blocks=[replace(b,id=uuid4().hex) for b in deepcopy(self.data)]
        items=list(song.timeline.blocks);items[index:index]=blocks;song.timeline.commit(items)
        song.timeline.selection={b.id for b in blocks}
        song.timeline.selected_step=next(s for b,s,e in song.timeline.ranges() if b.id==blocks[0].id)
    def copy_song(self,song):
        self.kind='song';self.data=deepcopy(song)
    def paste_song(self):
        if self.kind!='song':return None
        song=deepcopy(self.data);a=song.timeline
        a.blocks=tuple(replace(b,id=uuid4().hex) for b in a.blocks)
        a.selection.clear();a.selected_step=None;a.playhead=None;a.playing=False
        return song
