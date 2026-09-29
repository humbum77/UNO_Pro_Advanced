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
# Status levels for parameters the instrument automates but the statistical
# benchmark never covered. See the block near the bottom of this file.
UNORDERED='AUTOMATABLE: order position UNKNOWN'
NO_CAPTURE=('AUTOMATABLE: order position UNKNOWN; no clean capture possible, '
            'reached through the instrument menu')
def add(names,polarity,lo,hi,unit='',labels=(),status='CONFIRMED UI RANGE'):
    for name in names:PARAMETERS[name]=Parameter(polarity,lo,hi,unit,labels,status)
add(['CUTOFF 1','CUTOFF 2'],'unipolar',0,512)
add(['RESONANCE 1','RESONANCE 2'],'unipolar',0,127)
add(['LEVEL 1','LEVEL 2','LEVEL 3'],'unipolar',0,100)
add(['TUNE 1','TUNE 2','TUNE 3'],'bipolar',-24,24,'st',('+24 st','0','-24 st'),'PARTIAL: hybrid cents/semitone interpolation unknown')
add(['LFO 1','LFO 2'],'unipolar',0.01,99,'Hz',('99 Hz','49.5 Hz','0.01 Hz'),'PARTIAL: free-Hz only; sync mapping separate')
add(['WAVE 1','WAVE 2','WAVE 3'],'unipolar',None,None,labels=('UNKNOWN',),status='PARTIAL: normalized wave scale unknown')
add(['NOISE'],'unipolar',0,127,status='CONFIRMED parameter UI; held-Step Automation')
add(['SPACING','ENV AM 1','ENV AM 2'],'bipolar',-64,64)
add(['DRIVE AMOUNT'],'unipolar',0,127)
add(['MODULATION AMOUNT','DELAY AMOUNT','REVERB AMOUNT'],'unipolar',0,100)
add(['FM 1','FM 2'],'unipolar',0,100,status=NO_CAPTURE+'; candidate for the reported "filter fm"')
add(['VELOCITY'],'unipolar',1,127,status='CONFIRMED step parameter; NOT a held-Step Automation lane')

# Parameters the instrument also writes from automation, absent from the
# statistical benchmark. Reported by the operator 2026-09-29 as: OSC SYNC, ring,
# filter mode, filter fm, env_a, env_d, env_s, env_r, LFO_wave; then AENV and
# FENV A/D/S/R, F1_TRACK/F2_TRACK and GLIDE. None of them is in the confirmed
# order, so none is placed in AUTOMATION_ORDER.
#
# Status levels used here:
#   UNORDERED   automatable, position unknown, a clean capture is possible
#   NO_CAPTURE  automatable, position unknown, a clean capture is impossible
# NO_CAPTURE applies to the parameters reached through the instrument menu;
# the operator stated on 2026-09-29 that clean snapshots cannot be taken of
# them, so they can never be validated by the test suite. Both constants are
# defined at the top of this file.
add(['RING','OSC 2 SYNC','OSC 3 SYNC'],'unipolar',0,127,status=NO_CAPTURE)
add(['FILTER 1 MODE'],'unipolar',0,100,labels=('LP 0','LP 180','HP 0','HP 180','BYPASS'),status=NO_CAPTURE+'; enumerated 0,25,50,75,100')
add(['FILTER 2 MODE'],'unipolar',0,100,labels=('2P SERIES','4P SERIES','2P PARALLEL','4P PARALLEL','BYPASS SERIES','BYPASS PARALLEL'),status=NO_CAPTURE+'; enumerated 0,20,40,60,80,100')
add(['LFO 1 WAVE','LFO 2 WAVE'],'unipolar',0,127,labels=('SINE','TRIANGLE','UP SAW','DOWN SAW','SQUARE','RANDOM','S&H','NOISE'),status=UNORDERED)
add(['AMP ENV ATTACK','AMP ENV DECAY','AMP ENV SUSTAIN','AMP ENV RELEASE'],'unipolar',0,127,status=UNORDERED)
add(['FILTER ENV ATTACK','FILTER ENV DECAY','FILTER ENV SUSTAIN','FILTER ENV RELEASE'],'unipolar',0,127,status=UNORDERED)
add(['FILTER 1 KEY TRACKING','FILTER 2 KEY TRACKING'],'unipolar',0,127,status=NO_CAPTURE+'; the editor draws no control for these, so the range is unconfirmed')
add(['GLIDE'],'unipolar',0,127,status=NO_CAPTURE)
# The operator wrote "filter fm". Two candidates exist and they are different
# parameters: FM 1/FM 2 are the oscillator FM amounts (CC 25/26, registered
# above), Filter 1/2 Env Amount are the filter envelope amounts (CC 31/38).
# Both are registered; which one was meant is UNRESOLVED.
add(['FILTER 1 ENV AMOUNT','FILTER 2 ENV AMOUNT'],'unipolar',0,127,status=NO_CAPTURE+'; candidate for the reported "filter fm"')

# Held-Step Automation order, confirmed by the operator on 2026-09-29.
# NOISE is automatable and sits between LEVEL 3 and CUTOFF 1.
AUTOMATION_ORDER=('WAVE 1','TUNE 1','WAVE 2','TUNE 2','WAVE 3','TUNE 3',
 'LEVEL 1','LEVEL 2','LEVEL 3','NOISE','CUTOFF 1','RESONANCE 1','ENV AM 1',
 'CUTOFF 2','RESONANCE 2','ENV AM 2','SPACING','LFO 1','LFO 2',
 'DRIVE AMOUNT','MODULATION AMOUNT','DELAY AMOUNT','REVERB AMOUNT')
# Per-step parameters. Velocity is one of these and is not an automation lane;
# it sits on the automation panel only because the GUI gave it no other home.
STEP_PARAMETERS=('GATE','ACC','TIE','VELOCITY','LENGTH')
# Automatable, but the 2026-09-29 order confirmation did not cover them.
# A clean capture of these is possible, so a test could in principle close them.
AUTOMATION_UNORDERED=('LFO 1 WAVE','LFO 2 WAVE',
 'AMP ENV ATTACK','AMP ENV DECAY','AMP ENV SUSTAIN','AMP ENV RELEASE',
 'FILTER ENV ATTACK','FILTER ENV DECAY','FILTER ENV SUSTAIN','FILTER ENV RELEASE')
# Automatable, but reached through the instrument menu. The operator stated on
# 2026-09-29 that clean snapshots cannot be taken, so these are permanently
# unverifiable by the test suite and must not acquire capture-based tests.
AUTOMATION_NO_CAPTURE=('OSC 2 SYNC','OSC 3 SYNC','RING',
 'FILTER 1 MODE','FILTER 2 MODE',
 'FM 1','FM 2','FILTER 1 ENV AMOUNT','FILTER 2 ENV AMOUNT',
 'FILTER 1 KEY TRACKING','FILTER 2 KEY TRACKING','GLIDE')
# Panel order: the confirmed device order, then the step parameter VELOCITY,
# then the automatable parameters whose order is not yet known.
AUTOMATABLE=(AUTOMATION_ORDER+('VELOCITY',)+AUTOMATION_UNORDERED
             +AUTOMATION_NO_CAPTURE)
# Maximum automation lanes on one step. Confirmed by the operator 2026-09-29.
# Single source of truth: the canonical decoder, the native container and the
# editor cap used to disagree (18, 18 and 16). AUTO_L2.unosyp decodes to 17
# lanes on step 1, so a 16 cap refuses a file the instrument itself produced.
# A step also carries 3 notes plus the step parameters GATE, ACC, TIE, VELOCITY
# and LENGTH; those are per-step, not automation lanes.
MAX_AUTOMATION_LANES_PER_STEP=20

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
