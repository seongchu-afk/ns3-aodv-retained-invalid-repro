"""Compile unchanged historical scientific sources against a clean ns-3.47 build."""
from pathlib import Path
import argparse,subprocess,hashlib
P=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--queue-observer',action='store_true');p.add_argument('--suite',choices=['all','handler','natural95','six'],default='all');p.add_argument('--ns3',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();B=a.ns3.resolve();W=a.work.resolve();W.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256((B/'src/aodv/model/aodv-routing-protocol.cc').read_bytes()).hexdigest()=='43b8ff9e5ccd4c737422de1ebb191c1913cdfb33259c1bb2dab6d9720d77c79e'
libs=[str(x) for x in sorted((B/'build/lib').glob('*.so')) if 'aodv' not in x.name]
assert libs,'Build the pinned ns-3.47 base first.'
def run(c):subprocess.run(c,check=True)
for group in ['handler','natural95','six']:
 if a.suite not in ['all',group]:continue
 S=P/'sources'/group;G=W/group;G.mkdir(exist_ok=True)
 base=['g++','-O3','-DNDEBUG','-std=c++23','-fPIC','-I'+str(S),'-I'+str(B/'build/include'),'-I'+str(B/'src/aodv/model'),'-DNS3_BUILD_PROFILE_OPTIMIZED']
 extra=[];excluded={'aodv-routing-protocol.cc.o'}
 if group=='natural95':
  run(base+['-c',str(S/'lifecycle-rtable.cc'),'-o',str(G/'lifecycle.o')]);extra=[str(G/'lifecycle.o')];excluded.add('aodv-rtable.cc.o')
  if a.queue_observer:
   queue=G/'aodv-rqueue.cc';queue.write_bytes((B/'src/aodv/model/aodv-rqueue.cc').read_bytes())
   subprocess.run(['patch',str(queue),str(P/'supplementary_observer/queue-observer.patch')],check=True)
   run(base+['-c',str(queue),'-o',str(G/'queue.o')]);extra.append(str(G/'queue.o'));excluded.add('aodv-rqueue.cc.o')
 objs=[str(x) for x in sorted((B/'cmake-cache/src/aodv').rglob('*.o')) if x.name not in excluded]
 assert objs,'ns-3 CMake object files missing'
 for v in ['stock','patch']:
  V=G/v;V.mkdir(exist_ok=True);obj=str(V/'routing.o');run(base+['-c',str(S/f'{v}-routing.cc'),'-o',obj]);run(['g++','-shared','-o',str(V/'libns3.47-aodv-optimized.so'),obj]+extra+objs+['-Wl,-rpath,'+str(B/'build/lib')]+libs)
 name='unit' if group=='handler' else 'observer'
 run(base+[str(S/f'{name}.cc'),'-o',str(G/name),'-L'+str(G/'stock'),'-Wl,-rpath,'+str(B/'build/lib'),'-Wl,--no-as-needed','-l:libns3.47-aodv-optimized.so']+libs)
print('Built original S1, S3 and S4 harnesses. S2 is the settings reference.')
