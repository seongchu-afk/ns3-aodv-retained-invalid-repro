from pathlib import Path
import json,csv,subprocess,time,os,hashlib,concurrent.futures,collections
P=Path(__file__).resolve().parent;B=P/'ns-3.47';S=P/'temporal_sources'
configs=[dict(name='baseline')]+[dict(name=f'{k}{v}',**{k:v}) for k,vals in {'retention':[5,30],'retries':[1,4],'queueLen':[16,256],'queueTime':[5,60],'trafficDuration':[.4,2,20,60]}.items() for v in vals]
jobs=[dict(config=c,version=v,run=r) for c in configs for v in ['stock','patch'] for r in [1,2,3]]
def run(j):
 c=j['config'];v=j['version'];name=f"{c['name']}-{v}-{j['run']}";d=P/'counterexample_runs'/name;d.mkdir(parents=True,exist_ok=True);prefix=d/'trace'
 fingerprint=hashlib.sha256((P/'bin/counterexample').read_bytes()+(P/'temporal_lib'/v/'libns3.47-aodv-optimized.so').read_bytes()+Path(__file__).read_bytes()+(S/'retained.csv').read_bytes()).hexdigest()
 if (d/'status.json').exists():
  cached=json.loads((d/'status.json').read_text());assert cached.get('fingerprint')==fingerprint,'stale temporal result';return cached
 env=dict(os.environ,LD_LIBRARY_PATH=str(P/'temporal_lib'/v)+':'+str(B/'build/lib'),MANET_AODV_REASON_TRACE=str(prefix)+'-reason.csv',MANET_AODV_LIFECYCLE_TRACE=str(prefix)+'-lifecycle.csv')
 cmd=[str(P/'bin/counterexample'),'--protocol=AODV','--fixture=retained',f'--mobility={S}/retained.csv',f'--out={prefix}',f"--run={j['run']}",'--arpDeadTimeout=3','--hello=1','--mainAt=18.5','--observationStop=100','--diagnostic=1']+[f'--{k}={x}' for k,x in c.items() if k!='name']
 if 'trafficDuration' in c:cmd.append('--mainPackets=0')
 start=time.time()
 try:
  with (d/'stdout.log').open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180)
  result=dict(j,fingerprint=fingerprint,command=cmd,exit_code=r.returncode,wall_s=time.time()-start)
  if r.returncode==0:
   q=list(csv.DictReader(open(str(prefix)+'-qualification.csv')));result['qualification_pass']=any(x['phase']=='perturb' and x['pass']=='1' for x in q)
   flows=list(csv.DictReader(open(str(prefix)+'-flows.csv')));result['flows']=flows
   events=list(csv.DictReader(open(str(prefix)+'-events.csv')));rx=[float(x['time']) for x in events if x['event']=='rx' and x['flow']=='1' and x['unique_or_send_ok']=='1'];result.update(main_first_rx_s=min(rx) if rx else None,main_last_rx_s=max(rx) if rx else None,right_censored_no_delivery=not bool(rx),observation_end_s=100)
   snapshots=collections.defaultdict(list)
   for x in csv.DictReader(open(str(prefix)+'-route-snapshots.csv')):snapshots[int(x['snapshot'])].append(x)
   cycles=[];reactivations=[];last={}
   for sid,ss in snapshots.items():
    active={int(x['node']):int(x['next_hop'].split('.')[-1])-1 for x in ss if x['present']=='1' and x['flag']=='0' and float(x['expiry'])>float(x['time'])}
    found=set()
    for a in active:
     path=[];cur=a
     while cur in active and cur!=3:
      if cur in path:
       cyc=path[path.index(cur):]
       if len(cyc)>=2:found.add(tuple(sorted(cyc)))
       break
      path.append(cur);cur=active[cur]
    if found:cycles.append({'time':float(ss[0]['time']),'snapshot':sid,'cycles':[list(x) for x in sorted(found)]})
    for x in ss:
     n=x['node'];flag=x['flag']
     if n in last and last[n]=='1' and flag=='0':reactivations.append({'time':float(x['time']),'node':n})
     last[n]=flag
   result.update(cycle_snapshot_count=len(cycles),first_cycle=cycles[0] if cycles else None,invalid_to_valid=reactivations,monitored_destination='10.1.1.4',snapshot_policy='synchronous post lifecycle mutation plus explicit perturbation; not global scheduler trace')
   (d/'cycles.json').write_text(json.dumps(cycles,indent=2))
 except Exception as e:result=dict(j,exit_code=-1,error=repr(e),wall_s=time.time()-start)
 (d/'status.json').write_text(json.dumps(result,indent=2));print(name,result['exit_code'],result.get('qualification_pass'),result.get('main_first_rx_s'),result.get('cycle_snapshot_count'),flush=True);return result
if __name__=='__main__':
 (P/'FROZEN_COUNTEREXAMPLE.json').write_text(json.dumps({'jobs':jobs,'design':'Original R16 retained mobility, no injected invalidation, HELLO true, mainAt18.5, baseline exactly4 packets, observation100s. One-factor settings: effective retention5/15/30, retry1/2/4 independent of fixed blacklist5.6s, queue16/64/256, queue time5/30/60, application durations0.4/2/20/60 at10pps. Three run substreams1/2/3; qualification requires natural retained INVALID and reachable alternative at first relevant RREQ. Sustained recovery criterion as temporal matrix; no artificial restoration.','hashes':{str(x.relative_to(P)):hashlib.sha256(x.read_bytes()).hexdigest() for x in S.iterdir() if x.suffix in ['.cc','.h','.csv']}},indent=2))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(run,jobs))
 (P/'COUNTEREXAMPLE_COMPLETE.json').write_text(json.dumps(r,indent=2))
 flat=[]
 for x in r:
  f=next((z for z in x.get('flows',[]) if z['flow']=='1'),{})
  flat.append(dict(config=x['config']['name'],version=x['version'],run=x['run'],exit_code=x['exit_code'],artificial_perturbation_qualified=None,main_sent=f.get('sent'),main_received=f.get('unique_received'),first_rx=x.get('main_first_rx_s'),last_rx=x.get('main_last_rx_s'),censored=x.get('right_censored_no_delivery'),cycle_snapshots=x.get('cycle_snapshot_count'),reactivations=len(x.get('invalid_to_valid',[]))))
 with (P/'counterexample_summary.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
