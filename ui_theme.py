"""Compatibility bridge to the single global UNO2.2 theme."""
import tkinter as tk
from live_creator.ui import theme as T
TOKENS={'dark':dict(background=T.L0,panel=T.L1,control=T.L2,border=T.EDGE,text=T.TEXT_HI,muted=T.TEXT_MD,primary=T.ACCENT,secondary=T.FOCUS_BLUE,primary_active=T.ACCENT_SOFT,play=T.PLAY_GREEN,rec=T.STOP_RED)}
current='dark'
def set_theme(name):
 global current
 current='dark'
def color(value): return value
def recolor_widgets(root,previous=None): return
class Widgets:
 def __getattr__(self,name):
  original=getattr(tk,name)
  if name not in ('Menu','Entry','Label','Button','Frame','Toplevel'):return original
  def create(*args,**kwargs):
   for key in ('bg','fg','background','foreground','activebackground','activeforeground','insertbackground','selectcolor','highlightbackground','highlightcolor'):
    if key in kwargs:kwargs[key]=color(kwargs[key])
   widget=original(*args,**kwargs)
   if name=='Toplevel':widget.configure(bg=T.L0)
   return widget
  return create
widgets=Widgets()
