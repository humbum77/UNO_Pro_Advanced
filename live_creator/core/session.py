"""64 independent songs, separate editor and transport contexts."""
import hashlib
from .arrangement import Arrangement

COLORS=('#795140','#496879','#627347','#755d7f','#8a7145','#427569','#775461')
def color_for(key):return COLORS[int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%len(COLORS)]

class Song:
    def __init__(self,index):
        self.name=f'Song {index+1:02d}';self.color=COLORS[index%len(COLORS)]
        self.timeline=Arrangement();self.delay=0;self.colors={}
    @property
    def duration(self):return self.timeline.length*60/self.timeline.tempo

class Session:
    def __init__(self):
        self.pads=[Song(i) for i in range(64)];self.selected=0
        self.global_settings={};self.controller_settings={}
        self.playing_pad=None;self.pending_pad=None;self.deadline=None;self.next_tick=None;self.start_step=1
    @property
    def song(self):return self.pads[self.selected]
    @property
    def active(self):return self.playing_pad is not None or self.pending_pad is not None
    def select_pad(self,index):
        if not 0<=index<64:raise ValueError('Invalid pad')
        self.selected=index
    def stop(self):
        if self.playing_pad is not None:self.pads[self.playing_pad].timeline.stop()
        self.playing_pad=self.pending_pad=self.deadline=self.next_tick=None
    def toggle(self,now):
        if self.active:self.stop();return
        a=self.song.timeline
        if not a.length:return
        self.start_step=next((s for b,s,e in a.ranges() if a.selected_step is not None and s<=a.selected_step<=e),1)
        if a.loop_range and not a.loop_range[0]<=self.start_step<=a.loop_range[1]:self.start_step=a.loop_range[0]
        self.pending_pad=self.selected;self.deadline=now+self.song.delay
        self.update(now)
    def update(self,now):
        if self.pending_pad is not None and now>=self.deadline:
            self.playing_pad=self.pending_pad;self.pending_pad=None;self.deadline=None
            a=self.pads[self.playing_pad].timeline;a.playhead=self.start_step;a.playing=True;self.next_tick=now+60/a.tempo
        if self.playing_pad is not None:
            a=self.pads[self.playing_pad].timeline
            if not a.playing:self.stop();return
            while self.next_tick is not None and now>=self.next_tick:
                a.advance()
                if not a.playing:self.stop();break
                self.next_tick+=60/a.tempo
