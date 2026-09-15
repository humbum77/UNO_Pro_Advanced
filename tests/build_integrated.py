"""Committed, versioned source release. No user data/reference archives."""
from pathlib import Path
import hashlib,json,subprocess,zipfile,datetime
ROOT=Path(__file__).resolve().parents[1]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def main():
 if git('branch','--show-current')!='main':raise RuntimeError('Integrated build requires main')
 if git('status','--porcelain'):raise RuntimeError('Commit all release changes before build')
 version=(ROOT/'VERSION').read_text().strip();name='UNO_Pro_Advanced_v'+version
 release=ROOT/'builds'/name
 archive=ROOT/'builds'/(name+'.zip')
 if release.exists() or archive.exists():raise RuntimeError('Historical build already exists')
 files=list(ROOT.glob('*.py'))+[ROOT/n for n in ('VERSION','AGENTS.md','README.md','README.ru.md','CHANGELOG.md','PROJECT_INDEX.md','run_editor.bat','install_dependencies.bat','state_decoder_map.json','Docs/requirements.txt','Docs/INTEGRATION_v0.9.6-beta.md')]
 files+=list((ROOT/'live_creator').rglob('*.py'))
 files+=[ROOT/'Docs'/n for n in ('PROJECT_STATE.md','DECISIONS.md','RELEASE_PREPARATION.md')]
 files+=[p for p in (ROOT/'Assets').rglob('*') if p.is_file()]
 files+=[p for p in (ROOT/'tests').glob('*.py') if p.name!='build_live_creator.py']
 for p in files:
  if p.suffix=='.py':compile(p.read_text(encoding='utf-8-sig'),str(p),'exec')
 release.mkdir(parents=True)
 manifest={}
 for p in sorted(set(files)):
  relative=p.relative_to(ROOT);data=p.read_bytes();target=release/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  manifest[relative.as_posix()]=hashlib.sha256(data).hexdigest()
 (release/'BUILD_COMMIT').write_text(git('rev-parse','HEAD')+'\n')
 (release/'BUILD_DATE').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n')
 (release/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(release.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(release.parent))
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for path,digest in manifest.items():assert hashlib.sha256(z.read(name+'/'+path)).hexdigest()==digest
  assert not any('__pycache__' in n or n.endswith(('.pyc','.unosyp','.log')) for n in z.namelist())
 print('BUILD / CRC / MANIFEST PASS:',archive)
 print('SOURCE COMMIT:',git('rev-parse','HEAD'))
if __name__=='__main__':main()
