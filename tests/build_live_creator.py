"""Reproducible source release. Run from the Live-Creator worktree."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    if branch!='live-creator': raise RuntimeError('Build requires live-creator branch')
    files=sorted((ROOT/'live_creator').rglob('*.py'))+[ROOT/'run_live_creator.py',ROOT/'run_live_creator.bat',ROOT/'Docs/LIVE_CREATOR_v0.3-alpha.md',ROOT/'tests/test_live_creator.py',ROOT/'tests/test_v02.py',ROOT/'tests/test_v03.py',ROOT/'tests/gui_smoke_v02.py',ROOT/'tests/build_live_creator.py']
    for path in files:
        if path.suffix=='.py':compile(path.read_text(encoding='utf-8-sig'),str(path),'exec')
    subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
    release=ROOT/'builds/Live_Creator_v0.3-alpha'
    release.mkdir(parents=True,exist_ok=True)
    manifest={}
    for path in files:
        relative=path.relative_to(ROOT)
        target=release/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        data=path.read_bytes(); target.write_bytes(data)
        manifest[relative.as_posix()]=hashlib.sha256(data).hexdigest()
    (release/'VERSION').write_text('0.3-alpha\n',encoding='utf-8')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (release/'BUILD_COMMIT').write_text(commit+'\n',encoding='utf-8')
    (release/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    archive=ROOT/'builds/Live_Creator_v0.3-alpha.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(release.rglob('*')):
            if path.is_file():z.write(path,path.relative_to(release.parent))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():
            assert hashlib.sha256(z.read(release.name+'/'+name)).hexdigest()==digest
        assert not any('__pycache__' in n or n.endswith('.pyc') for n in z.namelist())
    print(f'COMPILE PASS: {sum(p.suffix==".py" for p in files)} modules')
    print(f'ZIP / HASH PASS: {archive}')

if __name__=='__main__':main()
