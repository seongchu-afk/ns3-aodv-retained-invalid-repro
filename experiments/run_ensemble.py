from pathlib import Path
import json,hashlib,subprocess,os,time,csv,concurrent.futures,statistics,math,random,gzip,shutil
P=Path(__file__).resolve().parent; B=P/'ns-3.47'; E=P.parent/'prior_evidence'; h=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
old=json.loads((P/'mobility.json').read_text()); envs=[]
for j in old:
 path=P/j['path'];assert h(path)==j['sha256'];envs.append(dict(name=j['name'],family=j['family'],mobility=str(path),sha256=j['sha256']))
def run(j):
 key=f"{j['environment']}-run{j['run']}-{j['version']}";d=P/'runs'/key;d.mkdir(exist_ok=True); prefix=d/'trace';status=d/'status.json'
 fingerprint=h(P/'bin/ensemble')+h(P/j['version']/'libns3.47-aodv-optimized.so')+h(Path(__file__))+h(j['mobility'])
 if status.exists():
  cached=json.loads(status.read_text());assert cached.get('fingerprint')==fingerprint,'stale result: '+key;return cached
 env=dict(os.environ,LD_LIBRARY_PATH=str(P/j['version'])+':'+str(B/'build/lib'),MANET_AODV_REASON_TRACE=str(prefix)+'-reason.csv')
 cmd=[str(P/'bin/ensemble'),'--protocol=AODV','--arpDeadTimeout=3',f"--run={j['run']}",f"--scenario={j['environment']}",f"--mobility={j['mobility']}",f'--out={prefix}','--diagnostic=0']
 start=time.time()
 try:
  with (d/'stdout.log').open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=300)
  result=dict(j,command=cmd,exit_code=r.returncode,wall_s=time.time()-start,fingerprint=fingerprint)
  if r.returncode==0:
   flows=list(csv.DictReader(open(str(prefix)+'-flows.csv')));phy=list(csv.DictReader(open(str(prefix)+'-phy.csv')))
   result.update(planned=sum(int(x['planned']) for x in flows),received=sum(int(x['unique_received']) for x in flows),control_bytes=sum(int(x['routing_control_frame_bytes']) for x in phy),retry_frames=sum(int(x['retry_frames']) for x in phy))
   result['pdr']=result['received']/result['planned'];result['app_window_control_bytes']=sum(int(x['routing_control_frame_bytes']) for x in phy if 60<=int(x['second'])<180)
   control_air=0;control_frames=0;app_air=0;app_frames=0
   for x in csv.DictReader(open(str(prefix)+'-airtime.csv')):
    if x['kind'] in ['RREQ','RREP','RERR','RREP_ACK','HELLO']:
     control_air+=int(x['duration_ns']);control_frames+=1
     if 60<=float(x['time'])<180:app_air+=int(x['duration_ns']);app_frames+=1
   result.update(control_airtime_ns=control_air,control_frames=control_frames,app_window_control_airtime_ns=app_air,app_window_control_frames=app_frames)
   for x in d.glob('*.csv'):
    if x.stat().st_size>200000:
     with x.open('rb') as a,gzip.open(str(x)+'.gz','wb') as b:shutil.copyfileobj(a,b)
     x.unlink()
 except Exception as ex: result=dict(j,error=repr(ex),exit_code=-1,wall_s=time.time()-start)
 status.write_text(json.dumps(result,indent=2)); print(key,result['exit_code'],round(result['wall_s'],2),flush=True);return result
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
 if args.smoke:jobs=[dict(environment=envs[0]['name'],mobility=envs[0]['mobility'],run=101,version=v) for v in ['stock','patch']]
 else:jobs=[dict(environment=e['name'],mobility=e['mobility'],run=r,version=v) for e in envs for r in range(101,121) for v in ['stock','patch']]
 design={'n_pairs_per_fixed_environment':20,'run_ids':list(range(101,121)),'rng_seed':20261030,'wifi_first_stream':1000,'aodv_first_stream':2000,'mobility':envs,'application':'deterministic 5 flows, starts 60+0.17*i s, interval 0.1 s, stop 180 s; no app RNG','pairing':'same frozen mobility and application schedule; same assigned protocol/MAC streams but endogenous consumption may diverge','cost_windows':'Unprefixed control metrics are whole-run [0,210); app_window_ metrics are [60,180), consistent with historical active application window.', 'inference':'Conditional on six fixed mobility traces; independent run substreams, not 120 independently sampled mobility realizations. n=20 fixed before outcomes as feasible repeated-run precision study, not powered noninferiority study. 95% paired Student-t intervals and fixed-seed percentile bootstrap; zeros and negatives retained; no margin or noninferiority claim.','jobs':jobs,'hashes':{str(p.relative_to(P)):h(p) for p in [P/'bin/ensemble',P/'stock/libns3.47-aodv-optimized.so',P/'patch/libns3.47-aodv-optimized.so',Path(__file__)]}}
 if not args.smoke:(P/'FROZEN_ENSEMBLE.json').write_text(json.dumps(design,indent=2))
 start=time.time()
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(run,jobs))
 (P/('SMOKE.json' if args.smoke else 'ENSEMBLE_COMPLETE.json')).write_text(json.dumps({'wall_s':time.time()-start,'results':results},indent=2))
