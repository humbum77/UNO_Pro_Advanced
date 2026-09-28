"""Shared UnoLive application-data location; never a preset-library folder."""
import os
from pathlib import Path

def data_root():
    root=os.environ.get('LOCALAPPDATA')
    if not root:raise RuntimeError('LOCALAPPDATA is unavailable')
    return Path(root)/'UnoLive'

def state_path():return data_root()/'state'/'live_creator_state.json'
