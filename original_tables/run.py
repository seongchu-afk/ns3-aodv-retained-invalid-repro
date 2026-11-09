"""Run original manuscript fixtures; output and binaries stay outside release sources."""
from pathlib import Path
import argparse,subprocess,os,concurrent.futures
P=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--ns3',required=True,type=Path);p.add_argument('--work',required=True,type=Path);p.add_argument('--suite',choices=['all','handler','natural95','six'],default='all');p.add_argument('--jobs',type=int,default=2);a=p.parse_args();B=a.ns3.resolve();W=a.work.resolve()
def run(job):
 group,key,version,args=job;G=W/group;out=G/'runs';out.mkdir(exist_ok=True);prefix=out/key
 if Path(str(prefix)+'-events.csv').exists() or Path(str(prefix)+'-cases.csv').exists():raise RuntimeError('Output already exists: '+str(prefix))
 env=dict(os.environ,LD_LIBRARY_PATH=str(G/version)+':'+str(B/'build/lib'),MANET_QUEUE_TRACE=str(prefix)+'-queue.csv',MANET_AODV_REASON_TRACE=str(prefix)+'-reasons.csv',MANET_AODV_LIFECYCLE_TRACE=str(prefix)+'-lifecycle.csv',MANET_UNIT_PACKET_TRACE=str(prefix)+'-packets.csv')
 cmd=[str(G/('unit' if group=='handler' else 'observer')),'--out='+str(prefix)+('-cases.csv' if group=='handler' else '')]+args
 with Path(str(prefix)+'.log').open('w') as f:subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
 print('Completed '+group+'/'+key,flush=True)
jobs=[]
for v in ['stock','patch']:
 if a.suite in ['all','handler']:jobs.append(('handler',v,v,[]))
 if a.suite in ['all','natural95']:jobs.append(('natural95',v,v,['--protocol=AODV','--fixture=natural','--mobility='+str(P/'sources/natural95/natural.csv'),'--run=1','--arpDeadTimeout=3','--hello=1','--mainAt=18.5']))
 if a.suite in ['all','six']:
  for family in ['original','rwp']:
   for seed in [1,2,3]:jobs.append(('six',f'{family}{seed}-{v}',v,['--protocol=AODV','--arpDeadTimeout=3',f'--run={seed}','--scenario='+family,'--mobility='+str(P/f'mobility/{family}{seed}.csv'),'--diagnostic=1']))
with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:list(pool.map(run,jobs))
