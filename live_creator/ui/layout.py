"""Shared fixed 32+32 geometry. No hardware assumptions."""
import math

class Slots:
    margin=10
    row_height=66
    def __init__(self,width):self.pitch=max(1,(width-2*self.margin)/32)
    def point(self,step):
        return self.margin+((step-1)%32)*self.pitch,((step-1)//32)*self.row_height+25
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
    amount=.08+.05*(1+math.sin(now*2*math.pi/3))/2
    rgb=[int(color[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join(f'{round(c+(255-c)*amount):02x}' for c in rgb)

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
