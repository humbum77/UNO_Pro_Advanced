"""Separate editor, transport snapshot, assigned loop and active loop."""
import hashlib
from copy import deepcopy
from enum import Enum
from .arrangement import Arrangement

COLORS=('#795140','#496879','#627347','#755d7f','#8a7145','#427569','#775461')
def color_for(key):return COLORS[int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%len(COLORS)]

class Transport(str,Enum):
    STOPPED='STOPPED'
    COUNTDOWN='COUNTDOWN'
    PLAYING='PLAYING'
class Loop(str,Enum):
    NONE='NONE'
    ASSIGNED='ASSIGNED'
    ACTIVE='ACTIVE'

class Song:
    def __init__(self,index):
        self.name=f'Song {index+1:02d}';self.color=COLORS[index%len(COLORS)]
        self.timeline=Arrangement();self.delay=0;self.colors={};self.length=64
    def set_length(self,value):
        value=int(value)
        if not 1<=value<=64:raise ValueError('LENGTH must be 1..64')
        self.length=value

class Session:
    def __init__(self,resolver=None):
        self.pads=[Song(i) for i in range(64)];self.selected=0
        self.global_settings={};self.controller_settings={}
        self.resolver=resolver or (lambda reference:None)
        self.transport=Transport.STOPPED;self.loop_state=Loop.NONE
        self.playing_pad=None;self.pending_pad=None;self.deadline=None
        self.playback=None;self.position=0.;self.last_time=None;self.durations=[]
        self.playback_pad=None
        self.loop_range=None
    @property
    def song(self):return self.pads[self.selected]
    @property
    def active(self):return self.transport!=Transport.STOPPED
    def select_pad(self,index):
        if type(index)is not int or not 0<=index<64:raise ValueError('Invalid pad')
        self.selected=index
    def timing(self,song):
        durations=[]
        for b in song.timeline.blocks:
            count=min(b.length,song.length-len(durations))
            if count<=0:break
            beats=self.resolver(b.preset)
            if beats is None or beats<=0:return None
            durations.extend([beats*60/song.timeline.tempo]*count)
        return durations
    def duration(self,song):
        values=self.timing(song)
        return sum(values) if values is not None else None
    @property
    def current_step(self):
        elapsed=0
        for index,duration in enumerate(self.durations):
            elapsed+=duration
            if self.position<elapsed-1e-8:return index+1
        return len(self.durations) or None
    @property
    def playing_block_id(self):
        if self.transport!=Transport.PLAYING or self.playback is None:return None
        return next((b.id for b,s,e in self.playback.timeline.ranges() if s<=self.current_step<=e),None)
    def stop(self):
        self.transport=Transport.STOPPED;self.playing_pad=self.pending_pad=None
        self.deadline=None;self.last_time=None;self.loop_state=Loop.NONE
    def assign_loop(self):
        previous=self.song.timeline.loop_range
        self.song.timeline.toggle_loop()
        if self.playing_pad==self.selected or self.pending_pad==self.selected:
            target=self.song.timeline.loop_range
            if target:
                spans=[(s,e) for b,s,e in self.playback.timeline.ranges() if b.id in self.song.timeline.selection]
                if not spans:
                    self.song.timeline.loop_range=previous
                    raise ValueError('Selected blocks are not in the playing snapshot')
                target=(min(s for s,e in spans),max(e for s,e in spans))
            self.loop_range=self.clip_loop(target,len(self.durations))
            self.loop_state=Loop.ASSIGNED if self.loop_range else Loop.NONE
    def toggle(self,now):
        if self.transport==Transport.COUNTDOWN:self.stop();return
        if self.transport==Transport.PLAYING:
            self.update(now)
            if self.loop_state==Loop.ACTIVE:
                self.pads[self.playing_pad].timeline.loop_range=None
                self.loop_range=None;self.loop_state=Loop.NONE
            else:self.stop()
            return
        if not self.song.timeline.length:return
        values=self.timing(self.song)
        if values is None:raise ValueError('Sequence duration unknown — playback unavailable')
        self.playback=deepcopy(self.song);self.playback_pad=self.selected;self.durations=values
        a=self.playback.timeline
        step=next((s for b,s,e in a.ranges() if a.selected_step is not None and s<=a.selected_step<=e),1)
        if step>len(values):step=1
        self.position=sum(values[:step-1])
        self.loop_range=self.clip_loop(a.loop_range,len(values));self.loop_state=Loop.ASSIGNED if self.loop_range else Loop.NONE
        self.pending_pad=self.selected;self.deadline=now+self.song.delay
        self.transport=Transport.COUNTDOWN;self.update(now)
    @staticmethod
    def clip_loop(target,length):
        if target and target[0]<=length:return (target[0],min(target[1],length))
        return None
    def update(self,now):
        if self.transport==Transport.COUNTDOWN:
            if now<self.deadline:return
            self.playing_pad=self.pending_pad;self.pending_pad=None
            self.last_time=self.deadline;self.deadline=None;self.transport=Transport.PLAYING
        if self.transport!=Transport.PLAYING:return
        delta=max(0,now-self.last_time);self.last_time=now
        target=self.position+delta
        if self.loop_range:
            start,end=self.loop_range;lo=sum(self.durations[:start-1]);hi=sum(self.durations[:end])
            if self.loop_state==Loop.ASSIGNED and self.position<hi and target>=lo:self.loop_state=Loop.ACTIVE
            if self.loop_state==Loop.ACTIVE and target>=hi:target=lo+(target-hi)%(hi-lo)
        self.position=min(target,sum(self.durations))
        if self.position>=sum(self.durations):self.stop()
