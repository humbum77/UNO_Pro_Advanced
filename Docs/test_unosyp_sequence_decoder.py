from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import storage
def check(path,expected):
    seq=storage.load_binary_unosyp_sequence(path);assert seq is not None
    got=[(i+1,st.notes,st.velocity,st.note_velocities,st.note_extras) for i,st in enumerate(seq.steps) if st.notes]
    assert got==expected,(got,expected)
