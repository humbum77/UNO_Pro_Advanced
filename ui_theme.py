"""Semantic colors shared by main canvas and embedded Live Creator."""
import tkinter as tk
TOKENS={'dark':dict(background='#101417',panel='#1b2024',control='#22282d',border='#3b444a',text='#e7e9ea',muted='#8e989f',primary='#c9ced1',secondary='#4db8ff',primary_active='#30363a',play='#8ecb18',rec='#d83a3a')}
current='dark'
def set_theme(name):
 global current
 current='dark'
def color(value):
 return value

def recolor_widgets(root,previous=None):
 return

class Widgets:
 """Theme newly opened legacy Tk controls without changing their behavior."""
 def __getattr__(self,name):
  original=getattr(tk,name)
  if name not in ('Menu','Entry','Label','Button','Frame','Toplevel'):return original
  def create(*args,**kwargs):
   for key in ('bg','fg','background','foreground','activebackground','activeforeground','insertbackground','selectcolor','highlightbackground','highlightcolor'):
    if key in kwargs:kwargs[key]=color(kwargs[key])
   widget=original(*args,**kwargs)
   if name=='Toplevel':widget.configure(bg=TOKENS[current]['background'])
   return widget
  return create
widgets=Widgets()
