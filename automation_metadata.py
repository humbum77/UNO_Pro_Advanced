"""Device UI metadata, never a MIDI or native entry encoder."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Parameter:
    polarity: str
    minimum: float | None
    maximum: float | None
    unit: str = ''
    labels: tuple = ()
    status: str = 'CONFIRMED UI RANGE'
    def fraction(self,value):
        return (value-self.minimum)/(self.maximum-self.minimum)
    def value(self,fraction):
        return round(self.minimum+fraction*(self.maximum-self.minimum),2)
    def scale_labels(self):
        if self.labels:return self.labels
        if self.minimum is None:return ('UNKNOWN',)
        return tuple(f'{v:g}' for v in (self.maximum,(self.maximum+self.minimum)/2,self.minimum))

PARAMETERS={}
def add(names,polarity,lo,hi,unit='',labels=(),status='CONFIRMED UI RANGE'):
    for name in names:PARAMETERS[name]=Parameter(polarity,lo,hi,unit,labels,status)
add(['CUTOFF 1','CUTOFF 2'],'unipolar',0,512)
add(['RESONANCE 1','RESONANCE 2'],'unipolar',0,127)
add(['LEVEL 1','LEVEL 2','LEVEL 3'],'unipolar',0,100)
add(['TUNE 1','TUNE 2','TUNE 3'],'bipolar',-24,24,'st',('+24 st','0','-24 st'),'PARTIAL: hybrid cents/semitone interpolation unknown')
add(['LFO 1','LFO 2'],'unipolar',0.01,99,'Hz',('99 Hz','49.5 Hz','0.01 Hz'),'PARTIAL: free-Hz only; sync mapping separate')
add(['WAVE 1','WAVE 2','WAVE 3'],'unipolar',None,None,labels=('UNKNOWN',),status='PARTIAL: normalized wave scale unknown')
add(['SPACING','ENV AM 1','ENV AM 2'],'bipolar',-64,64)
add(['DRIVE AMOUNT'],'unipolar',0,127)
add(['MODULATION AMOUNT','DELAY AMOUNT','REVERB AMOUNT'],'unipolar',0,100)
AUTOMATABLE=tuple(PARAMETERS)
add(['FM 1','FM 2'],'unipolar',0,100,status='CONFIRMED parameter UI; NOT held-Step Automation')

def empty_lines():
    return [{'parameter':name,'values':[None]*64,'units':'device-ui'} for name in AUTOMATABLE]

def parameter_line(sequence,name):
    for lane in sequence.automation:
        if lane.get('parameter')==name:return lane
    lane={'parameter':name,'values':[None]*64,'units':'device-ui'}
    sequence.automation.append(lane)
    return lane

def display_value(lane,value):
    if value is None:return None
    # Legacy 7-bit samples stay opaque: no unconfirmed MIDI-to-device conversion.
    return value if lane.get('units')=='device-ui' else None
