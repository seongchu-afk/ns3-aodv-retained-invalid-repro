from pathlib import Path
import subprocess,json,os,csv,time
P=Path(__file__).resolve().parent;B=P/'ns-3.47';out=P/'handler_checks';out.mkdir(exist_ok=True);results=[]
for program in ['unit','transitions']:
 for v in ['stock','patch']:
  p=out/f'{program}-{v}';env=dict(os.environ,LD_LIBRARY_PATH=str(P/v)+':'+str(B/'build/lib'),MANET_AODV_REASON_TRACE=str(p)+'-reason.csv',MANET_INIT_TRACE='1')
  cmd=[str(P/'bin'/program),'--out='+str(p)+'.csv'];start=time.time()
  with open(str(p)+'.log','w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60)
  results.append(dict(program=program,version=v,exit_code=r.returncode,wall_s=time.time()-start,command=cmd))
(P/'HANDLER_COMPLETE.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
