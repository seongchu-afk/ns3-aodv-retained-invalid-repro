#!/usr/bin/env python3
"""One v2 entry point for analysis, a clean-build smoke check, or full simulation."""
from pathlib import Path
import argparse,subprocess,sys,json,shutil,datetime,hashlib,csv
P=Path(__file__).resolve().parent;E=P/'experiments'
def run(script,*args):subprocess.run([sys.executable,str(script),*map(str,args)],check=True)
def verify_manifest(root):
 data=json.loads((root/'MANIFEST.json').read_text())
 for f in data['files']:
  p=root/f['path'];assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'],f['path']
def analyze(root,out,check_reference):
 root=root.resolve();out=out.resolve();assert root!=out and root not in out.parents,'Output must be outside the input tree'
 if (root/'MANIFEST.json').exists():verify_manifest(root)
 run(P/'analysis/test_strict_returns.py')
 run(P/'analysis/analyze_temporal.py','--input-root',root,'--output-root',out)
 # The existing ensemble analysis is run in the output directory, never beside raw inputs.
 target=out/'ensemble';target.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(root/'ENSEMBLE_COMPLETE.json',target/'ENSEMBLE_COMPLETE.json')
 shutil.copyfile(E/'analyze_ensemble.py',target/'analyze_ensemble.py');run(target/'analyze_ensemble.py')
 actual=json.loads((out/'TEMPORAL_EXTENDED.json').read_text());assert len(actual)==195
 assert len({(x['suite'],x['case']) for x in actual})==195
 checks={'temporal_cases':195,'ensemble_runs':240,'strict_predicate_tests':15,'reference_equal':None}
 if check_reference:
  checks['reference_equal']={}
  for name in ['TEMPORAL_EXTENDED.json','temporal_extended_summary.csv','counterexample_summary.csv','combined_summary.csv','recovery_windows.csv']:
   assert (out/name).read_bytes()==(P/'reference'/name).read_bytes(),name;checks['reference_equal'][name]=True
  for name in ['paired_runs.csv','ensemble_summary.csv','ensemble_summary.json']:
   assert (target/name).read_bytes()==(P/'reference'/name).read_bytes(),name;checks['reference_equal'][name]=True
 (out/'VALIDATION.json').write_text(json.dumps(checks,indent=2)+'\n')
 print(json.dumps(checks,indent=2))
p=argparse.ArgumentParser();p.add_argument('mode',choices=['analysis','smoke','full']);p.add_argument('--input',type=Path);p.add_argument('--output',type=Path,default=P/'results');p.add_argument('--archive',type=Path);p.add_argument('--jobs',type=int,default=4);a=p.parse_args()
if a.mode=='analysis':
 if not a.input:p.error('analysis requires --input pointing to extracted analysis_data')
 analyze(a.input,a.output,True)
else:
 if not a.archive:p.error('smoke/full requires --archive pointing to official ns-3.47.tar.bz2')
 # Keep previous observations, but never use their simulation cache on a fresh workflow.
 backup=E/('previous_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
 names=['runs','temporal_runs','counterexample_runs','combined_runs','handler_checks']
 existing=[E/n for n in names if (E/n).exists()]
 if existing:
  backup.mkdir()
  for d in existing:shutil.move(d,backup/d.name)
 run(E/'build.py','--archive',a.archive,'--jobs',a.jobs)
 run(E/'run_handler_checks.py')
 handlers=json.loads((E/'HANDLER_COMPLETE.json').read_text())
 assert len(handlers)==4 and all(x['exit_code']==0 for x in handlers)
 for ref in sorted((P/'reference/handler_checks').glob('*.csv')):
  assert (E/'handler_checks'/ref.name).read_bytes()==ref.read_bytes(),'handler mismatch: '+ref.name
 if a.mode=='smoke':
  run(E/'run_ensemble.py','--smoke');run(E/'smoke_fixtures.py');run(P/'analysis/test_strict_returns.py')
  expected=json.loads((P/'reference/smoke_expected.json').read_text())
  rows=json.loads((E/'SMOKE.json').read_text())['results'];assert len(rows)==2
  for x in rows:
   assert x['exit_code']==0
   for k,v in expected[x['version']].items():assert x[k]==v,('ensemble smoke mismatch',x['version'],k,x[k],v)
  print('PASS: all 12 handler CSVs, 20 ensemble metric values and five fixture outcomes match the frozen reference.')
 else:
  for name in ['run_temporal.py','run_counterexample.py','run_combined.py','run_ensemble.py']:run(E/name)
  analyze(E,a.output,True)
