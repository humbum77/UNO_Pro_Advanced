"""Global UNO2.2 UI theme tokens. Visual pad palette remains component-local."""
L0='#0d1114'
L1='#232a2f'
L2='#22292f'
L3='#2b333a'
L4='#2f373e'
DIVIDER='#2a3138'
EDGE='#3b444a'
EDGE_HI='#4a545c'
TEXT_HI='#e7e9ea'
TEXT_MD='#a8b0b6'
TEXT_LO='#5f686e'
TEXT_DIS='#3f474d'
ACCENT='#ff9d2e'
ACCENT_TEXT='#0d1114'
ACCENT_SOFT='#3a2a15'
PLAY_GREEN='#8ecb18'
STOP_RED='#d83a3a'
FOCUS_BLUE='#4db8ff'
OK='#7ed957'; WARN='#ffb84d'; ERROR='#ff5c5c'; INFO='#4db8ff'
FONT_FAMILY='Segoe UI'; FONT_MONO='Consolas'
TITLE=(FONT_FAMILY,11,'bold'); SUBTITLE=(FONT_FAMILY,10,'bold'); LABEL=(FONT_FAMILY,9); LABEL_UP=(FONT_FAMILY,9,'bold'); VALUE=(FONT_MONO,10); BODY=(FONT_FAMILY,10); SMALL=(FONT_FAMILY,8); TINY=(FONT_FAMILY,7)
R_SM=4; R_MD=8; R_LG=12
S1=4; S2=8; S3=12; S4=16; S5=24; S6=32
SHADOW='#000000'; SHADOW_ALPHA=90
ROW_H=24; BUTTON_H=30; BUTTON_H_LG=40; FIELD_H=28; TAB_H=32; HEADER_H=40
# backwards compatibility
BG=L0; PANEL=L1; PANEL2=L2; TEXT=TEXT_HI; MUTED=TEXT_MD; ORANGE=ACCENT; ORANGE2=ACCENT_SOFT
LIGHT_GREY='#c9ced1'; GREEN=PLAY_GREEN; RED=STOP_RED; BLUE=FOCUS_BLUE

def mix(a,b,t):
    t=max(0.0,min(1.0,t)); av=[int(a.lstrip('#')[i:i+2],16) for i in (0,2,4)]; bv=[int(b.lstrip('#')[i:i+2],16) for i in (0,2,4)]
    return '#'+''.join(f'{round(x+(y-x)*t):02x}' for x,y in zip(av,bv))
def shade(c,f):
    c=c.lstrip('#');v=[int(c[i:i+2],16) for i in (0,2,4)];return '#'+''.join(f'{max(0,min(255,round(n*f))):02x}' for n in v)
def contrast(c):
    c=c.lstrip('#');v=[int(c[i:i+2],16)/255 for i in (0,2,4)];lin=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v];lum=sum(a*b for a,b in zip(lin,(.2126,.7152,.0722)));return '#101417' if lum>.179 else '#ffffff'
