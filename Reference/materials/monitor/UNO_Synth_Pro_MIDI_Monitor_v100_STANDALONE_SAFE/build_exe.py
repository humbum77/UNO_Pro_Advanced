from pathlib import Path
import sys
try:
    import PyInstaller.__main__
except ImportError:
    print("Install PyInstaller: python -m pip install pyinstaller")
    sys.exit(1)
script = Path(__file__).with_name("uno_midi_monitor_winapi.py")
PyInstaller.__main__.run([
    str(script), "--onefile", "--noconsole",
    "--name=UNO_Synth_Pro_MIDI_Monitor",
    "--hidden-import=tkinter", "--hidden-import=ctypes",
    "--clean", "--noconfirm",
])
