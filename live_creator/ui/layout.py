"""Shared fixed 32+32 geometry. No hardware assumptions."""
import math

class Slots:
    margin=10
    row_height=86
    def __init__(self,width):self.pitch=max(1,(width-2*self.margin)/32)
    def point(self,step):
        return self.margin+((step-1)%32)*self.pitch,((step-1)//32)*self.row_height+45
    def position(self,x,y):
        row=max(0,min(1,int(y//self.row_height)))
        return row*32+max(0,min(32,(x-self.margin)/self.pitch))+1
    def segments(self,start,end):
        for row in range(2):
            first=max(start,row*32+1);last=min(end,row*32+32)
            if first<=last:
                x,y=self.point(first)
                yield x,y,x+(last-first+1)*self.pitch,y+30,first,last

def pulse(color,now):
    import colorsys
    rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    hue,light,saturation=colorsys.rgb_to_hls(*rgb)
    wave=(1+math.sin(now*2*math.pi/2.4))/2
    # Wide luminance sweep, including high-lightness fills, without a hue shift.
    def luminance(rgb):
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(a*b for a,b in zip(linear,(.2126,.7152,.0722)))
    low=max(.23,min(.53,luminance(rgb)+.03));target=low+.24*wave
    left,right=0.,1.
    for _ in range(14):
        middle=(left+right)/2
        if luminance(colorsys.hls_to_rgb(hue,middle,saturation))<target:left=middle
        else:right=middle
    rgb=colorsys.hls_to_rgb(hue,(left+right)/2,saturation)
    return '#'+''.join(f'{round(c*255):02x}' for c in rgb)

def clipped(text,width,font):
    if font.measure(text)<=width:return text
    while text and font.measure(text+'…')>width:text=text[:-1]
    return text+'…' if width>=font.measure('…') else ''

def wrapped(text,width,lines,font):
    words=text.split();result=[];line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if line and font.measure(candidate)>width:result.append(line);line=word
        else:line=candidate
    if line:result.append(line)
    if len(result)>lines:result=result[:lines-1]+[' '.join(result[lines-1:])]
    return '\n'.join(clipped(line,width,font) for line in result)
