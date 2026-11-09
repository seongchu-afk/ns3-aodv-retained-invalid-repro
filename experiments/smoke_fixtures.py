"""Small clean-room QA subset. Not an additional scientific expansion."""
from pathlib import Path
import importlib.util,json,csv,time,hashlib,platform,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"analysis"))
from strict_returns import detect_returns
P=Path(__file__).resolve().parent;start=time.time();checks=[]
def load(name):
 spec=importlib.util.spec_from_file_location(name,P/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
for suite,variants in [('counterexample',['stock','patch']),('temporal',['stock','patch','unsafe'])]:
 m=load('run_'+suite)
 for v in variants:
  r=m.run({'config':{'name':'baseline'},'version':v,'run':1});assert r['exit_code']==0,r
  d=P/(suite+'_runs')/f'baseline-{v}-1';flows=list(csv.DictReader(open(d/'trace-flows.csv')));main=next(x for x in flows if x['flow']=='1');received=int(main['unique_received'])
  expected=(0 if v=='stock' else 4) if suite=='counterexample' else(271 if v=='unsafe' else 195)
  assert received==expected,(suite,v,received,expected)
  reasons=list(csv.DictReader(open(d/'trace-reason.csv')));relevant=[x for x in reasons if x['node']=='1' and x['origin']=='10.1.1.1' and x['destination']=='10.1.1.4' and float(x['time'])>=18.5 and x['reason']=='destination_route_present']
  retained=bool(relevant and relevant[0]['route_flag']=='1' and relevant[0]['next_hop']=='10.1.1.1' and float(relevant[0]['route_lifetime'])>0)
  if suite=='counterexample':assert retained,'Natural retained-state prerequisite failed'
  strict=detect_returns(d/'trace-control-events.csv');returned=set(strict['source_main_sequences'])
  if suite=='temporal':
   assert r['qualification_pass']
   assert (r['cycle_snapshot_count']>0)==(v=='unsafe')
   assert len(returned)==(32 if v=='unsafe' else 0)
  checks.append({'suite':suite,'variant':v,'run':1,'planned':int(main['planned']),'received':received,'retained_state_qualified':retained if suite=='counterexample' else None,'positive_perturbation_qualified':r.get('qualification_pass') if suite=='temporal' else None,'cycle_snapshot_count':r['cycle_snapshot_count'],'physical_returned_sequences':len(returned),'status':'passed','binary_sha256':hashlib.sha256((P/'bin'/suite).read_bytes()).hexdigest()})
result={'status':'passed','wall_s':time.time()-start,'python':platform.python_version(),'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],'checks':checks}
(P/'SMOKE_FIXTURES.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
