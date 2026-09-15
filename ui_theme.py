"""Semantic colors shared by main canvas and embedded Live Creator."""
import tkinter as tk
TOKENS={
 'dark':dict(background='#101417',panel='#1b2024',control='#22282d',border='#3b444a',text='#e7e9ea',muted='#8e989f',primary='#ff8c18',secondary='#4db8ff',primary_active='#8a4b12',play='#65b938',rec='#d83a3a'),
 'light':dict(background='#edf0f2',panel='#fafbfc',control='#e0e5e9',border='#a6b0b8',text='#20292f',muted='#596873',primary='#4db8ff',secondary='#ff8c18',primary_active='#c4e4f7',play='#65b938',rec='#d83a3a')}
current='dark'
def set_theme(name):
 global current
 current=name if name in TOKENS else 'dark'
def color(value):
 if not isinstance(value,str) or current=='dark':return value
 baseline=TOKENS['dark'];target=TOKENS[current]
 for key,v in baseline.items():
  if value.lower()==v:return target[key]
 # Existing muted canvas backgrounds/grid colors (not note/preset colors).
 shades={'#0d1113':'background','#0b0f11':'control','#090c0e':'control','#11171a':'panel','#10171a':'panel','#0a0e10':'control','#30363a':'control','#263238':'border','#2d3a40':'border','#344148':'border','#435057':'border','#56636a':'border','#c9ced1':'text'}
 return target[shades[value.lower()]] if value.lower() in shades else value

def recolor_widgets(root,previous):
 old=TOKENS[previous];new=TOKENS[current]
 mapping={v:new[k] for k,v in old.items()}
 def visit(widget):
  for key in ('background','foreground','insertbackground','highlightbackground','highlightcolor','activebackground','activeforeground'):
   try:
    value=str(widget.cget(key)).lower()
    if value in mapping:widget.configure(**{key:mapping[value]})
   except tk.TclError:pass
  for child in widget.winfo_children():visit(child)
 visit(root)

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
