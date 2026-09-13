"""UNO Synth Pro protocol map.
Only monitor/manual-confirmed mappings are enabled for live output.
Unknown bulk-store semantics remain intentionally locked.
"""
IK_HEADER = bytes([0xF0,0x00,0x21,0x1A,0x02,0x03])
STATE_READ = bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x37,0x00,0x00,0xF7])
PRESET_NAME_READ_PREFIX = bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x24,0x01])
PRESET_PAGE_READ_PREFIX = bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x29])
def preset_name_read(slot):
    n=max(1,min(256,int(slot)))-1
    return PRESET_NAME_READ_PREFIX+bytes([n//128,n%128,0xF7])
def preset_page_read(slot,page):
    n=max(1,min(256,int(slot)))-1;page=max(0,min(4,int(page)))
    return PRESET_PAGE_READ_PREFIX+bytes([n//128,n%128,page,0xF7])
COMMANDS={0x24:'preset name/info',0x28:'bulk preset-state write/store (LOCKED)',0x29:'hardware preset/page read',0x32:'current preset notification',0x33:'preset select/load (partial)',0x36:'current-buffer load (EXPERIMENTAL / not hardware-confirmed)',0x37:'current state read'}
CC={
 'BANK':0,'MOD_WHEEL':1,'GLIDE':5,'VCA':7,'SWING':9,
 'OSC1_WAVE':12,'OSC2_WAVE':13,'OSC3_WAVE':14,
 'OSC1_TUNE':15,'OSC2_TUNE':16,'OSC3_TUNE':17,
 'OSC1_LEVEL':18,'OSC2_LEVEL':19,'OSC3_LEVEL':20,'NOISE_LEVEL':21,
 'SYNC2':22,'SYNC3':23,'RING':24,'FM12':25,'FM13':26,
 'F1_CUTOFF':28,'F1_RES':29,'F1_MODE':30,'F1_ENV':31,'F1_TRACK':32,
 'F2_CUTOFF':35,'F2_RES':36,'F2_MODE':37,'F2_ENV':38,'F2_TRACK':39,
 'FILTER_SPACING':40,'FILTER_LINK':41,
 'LFO1_WAVE':44,'LFO1_RATE':45,'LFO1_FADE':46,'LFO1_SYNC':47,
 'LFO2_WAVE':48,'LFO2_RATE':49,'LFO2_FADE':50,'LFO2_SYNC':51,
 'FENV_A':53,'FENV_D':54,'FENV_S':55,'FENV_R':56,'FENV_LOOP':57,'FENV_RETRIG':58,
 'AENV_A':59,'AENV_D':60,'AENV_S':61,'AENV_R':62,'AENV_LOOP':63,
 # Modulation Matrix Amount slots 1..16 (official MIDI chart: CC66..81)
 **{f'MAMT{i}':66+i for i in range(16)},
 # FX (official MIDI chart v1.0.0, page 3)
 'DRIVE':90,'REV_AMOUNT':91,'DELAY_AMOUNT':92,'MOD_AMOUNT':93,
 'MOD_TYPE':95,'MOD_INTENSITY':96,'MOD_RATE':97,'CHORUS_MODE':98,
 'DELAY_TYPE':100,'DELAY_SYNC':101,'DELAY_TIME':102,'DELAY_TIME_R':103,
 'DELAY_FEEDBACK':104,'DELAY_LPF':105,
 'REVERB_TYPE':107,'REV_PRE':108,'REV_TIME_SPECIAL':109,'REV_LOW':110,
 'REV_TIME':111,'REV_HIGH':112,'REV_SIZE':113,'REV_FILTER':114,
}
CC_TO_KEY={v:k for k,v in CC.items()}
SEQ_STATE={'direction_offset':219,'direction_mask':0x30,'direction_values':{0x00:'Forward',0x10:'Backward',0x20:"Back'n'Forth"},'tie_offset':220,'tie_mask':0x10,'gate_offsets':(220,221),'gate_scale':32,'accent_offset':223}
ARP_SYSEX={'direction_prefix':bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x3C,0x00,0x00]),'octaves_prefix':bytes([0xF0,0x00,0x21,0x1A,0x02,0x03,0x3C,0x00,0x01])}
ARP_MODES=['UP','DOWN','U/D','UD+','D/U','DU+','RND','PLY','X2U','X2D']
FILTER1_MODES=['LP 0°','LP 180°','HP 0°','HP 180°','BYPASS']
FILTER1_MODE_RAW=[0,25,50,75,100]
FILTER2_MODES=['2P SERIES','4P SERIES','2P PARALLEL','4P PARALLEL','BYPASS SERIES','BYPASS PARALLEL']
FILTER2_MODE_RAW=[0,20,40,60,80,100]
FILTER_LINK_RAW={'OFF':0,'CUTOFF':64,'CUT+RES':127}
# Monitor-confirmed bipolar encodings: Spacing/F1 Env/F2 Env -63..+64 <-> raw 0..127 (0 at raw 63); Key Tracking -200..+200 <-> raw 0..127 (0 at raw 63).
MOD_TYPES=['CHORUS','PHASER','FLANGER']
MOD_TYPE_RAW=[0,42,84]
DELAY_TYPES=['MONO','STEREO','DOUBLER','PING PONG','LCR']
DELAY_TYPE_RAW=[0,25,50,75,100]
REVERB_TYPES=['HALL','PLATE','REVERSE','SPRING']
REVERB_TYPE_RAW=[0,32,64,96]
LFO_SHAPES=['SINE','TRIANGLE','UP SAW','DOWN SAW','SQUARE','RANDOM','S&H','NOISE']
SEQ_DIRECTIONS=['Forward','Backward',"Back'n'Forth"]

def norm(v,lo,hi):
    if hi==lo:return 0
    return max(0,min(127,round((float(v)-lo)*127/(hi-lo))))
def denorm(v,lo,hi): return lo+(max(0,min(127,int(v)))/127.0)*(hi-lo)

def decode_preset_name_response(data):
    data=bytes(data)
    if len(data)<12 or data[:6]!=IK_HEADER or len(data)<43 or data[7]!=0x24:
        return None
    slot=(data[9]&0x7F)*128+(data[10]&0x7F)+1
    if not 1<=slot<=256:return None
    raw=data[11:-1].split(b'\x00',1)[0]
    return slot,raw.decode('ascii','ignore').strip()
