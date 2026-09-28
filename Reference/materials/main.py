import logging
from logging.handlers import RotatingFileHandler
import storage
from app import App

def _configure_logging():
 root=logging.getLogger()
 root.setLevel(logging.WARNING)
 fmt=logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
 try:
  # Explicit startup initialization: storage import itself remains side-effect free.
  storage.ensure_dirs()
  handler=RotatingFileHandler(storage.ROOT/'editor.log',maxBytes=512*1024,backupCount=2,encoding='utf-8')
 except OSError:
  # Logging must never prevent the editor from starting if Documents is unavailable/unwritable.
  handler=logging.StreamHandler()
 handler.setFormatter(fmt)
 root.addHandler(handler)

if __name__=='__main__':
 _configure_logging()
 App().mainloop()
