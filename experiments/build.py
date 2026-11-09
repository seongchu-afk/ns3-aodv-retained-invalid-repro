"""Build unmodified ns-3.47, then the separately instrumented research harnesses."""
from pathlib import Path
import subprocess,json,hashlib,argparse,os,time,shutil
P=Path(__file__).resolve().parent;B=P/'ns-3.47'
def run(cmd):
 print(' '.join(map(str,cmd)),flush=True)
 subprocess.run(list(map(str,cmd)),check=True,cwd=P)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,required=True);parser.add_argument('--jobs',type=int,default=4);a=parser.parse_args()
assert sha(a.archive)=='8b3adca956c834ea436b915986ab8fd053e90041acae7426895d595aaa3ccc39','Wrong official source archive'
if not B.exists():run(['tar','-xjf',a.archive.resolve(),'-C',P])
assert sha(B/'src/aodv/model/aodv-routing-protocol.cc')=='43b8ff9e5ccd4c737422de1ebb191c1913cdfb33259c1bb2dab6d9720d77c79e','Upstream source modified'
subprocess.run(['./ns3','configure','--build-profile=optimized','--enable-modules=aodv,wifi,mobility,applications,flow-monitor,olsr,dsdv,dsr','--disable-examples','--disable-tests'],cwd=B,check=True)
subprocess.run(['./ns3','build','-j',str(a.jobs)],cwd=B,check=True)
for sub in ['bin','stock','patch','runs','temporal_lib/stock','temporal_lib/patch','temporal_lib/unsafe']:(P/sub).mkdir(parents=True,exist_ok=True)
libs=[x for x in (B/'build/lib').glob('*.so') if 'aodv' not in x.name]
commands=[]
def base(S):return ['g++','-O3','-DNDEBUG','-std=c++23','-fPIC','-I'+str(S),'-I'+str(B/'build/include'),'-I'+str(B/'src/aodv/model'),'-DNS3_BUILD_PROFILE_OPTIMIZED']
S=P/'sources'
for v in ['stock','patch']:
 commands.append(base(S)+['-c',str(S/f'{v}-routing.cc'),'-o',str(P/f'{v}.o')])
 objs=[str(x) for x in (B/'cmake-cache/src/aodv').rglob('*.o') if x.name!='aodv-routing-protocol.cc.o']
 commands.append(['g++','-shared','-o',str(P/v/'libns3.47-aodv-optimized.so'),str(P/f'{v}.o')]+objs+['-L'+str(B/'build/lib'),'-Wl,-rpath,'+str(B/'build/lib')]+[str(x) for x in libs])
for name in ['ensemble','unit','transitions']:
 commands.append(base(S)+[str(S/f'{name}.cc'),'-o',str(P/'bin'/name),'-L'+str(P/'stock'),'-Wl,-rpath,'+str(B/'build/lib'),'-Wl,--no-as-needed','-l:libns3.47-aodv-optimized.so']+[str(x) for x in libs])
S=P/'temporal_sources'
commands.append(base(S)+['-c',str(S/'lifecycle-rtable.cc'),'-o',str(S/'lifecycle.o')])
for v in ['stock','patch','unsafe']:
 commands.append(base(S)+['-c',str(S/f'{v}-routing.cc'),'-o',str(S/f'{v}.o')])
 objs=[str(x) for x in (B/'cmake-cache/src/aodv').rglob('*.o') if x.name not in ['aodv-routing-protocol.cc.o','aodv-rtable.cc.o']]
 commands.append(['g++','-shared','-o',str(P/'temporal_lib'/v/'libns3.47-aodv-optimized.so'),str(S/f'{v}.o'),str(S/'lifecycle.o')]+objs+['-Wl,-rpath,'+str(B/'build/lib')]+[str(x) for x in libs])
for name in ['temporal','counterexample','combined']:
 commands.append(base(S)+[str(S/f'{name}.cc'),'-o',str(P/'bin'/name),'-L'+str(P/'temporal_lib/stock'),'-Wl,-rpath,'+str(B/'build/lib'),'-Wl,--no-as-needed','-l:libns3.47-aodv-optimized.so']+[str(x) for x in libs])
(P/'BUILD_COMMANDS.json').write_text(json.dumps(commands,indent=2))
for cmd in commands:run(cmd)
