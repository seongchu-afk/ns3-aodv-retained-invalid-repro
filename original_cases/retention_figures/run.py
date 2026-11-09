#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Execute exactly the 24 frozen whole-run jobs, with no retiming or automatic retry."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
P = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--work',type=Path,required=True); a=parser.parse_args(); W=a.work.resolve()
    if W==P or P in W.parents: parser.error('--work must be outside the public candidate')
    build=json.loads((W/'build.json').read_text()); B=Path(build['ns3']); config=json.loads((P/'config/matrix.json').read_text())
    for name,digest in build['binaries'].items(): assert sha(W/name)==digest, 'Built binary changed'
    for name,digest in build['research_sources'].items(): assert sha(P/name)==digest, 'Research source changed after compilation'
    for name,digest in build['reused_clean_non_aodv_libraries'].items(): assert sha(B/name)==digest, 'Clean base library changed'
    assert not (W/'runs').exists(), 'Use a fresh run directory; no overwriting or automatic retries'
    (W/'runs').mkdir(); records=[]
    frozen=dict(config=config,binaries=build['binaries'],inputs={str(x.relative_to(P)):sha(x) for x in sorted((P/'config').glob('*'))})
    (W/'FROZEN.json').write_text(json.dumps(frozen,indent=2)+'\n')
    try:
        for j in config['jobs']:
            key=f"{j['case']}-{j['seed']}-{j['version']}"; prefix=W/'runs'/key; env=dict(os.environ)
            env['LD_LIBRARY_PATH']=str(W/j['version'])+':'+str(B/'build/lib')
            env['MANET_AODV_REASON_TRACE']=str(prefix)+'-reason.csv'; env['MANET_AODV_LIFECYCLE_TRACE']=str(prefix)+'-lifecycle.csv'
            command=[str(W/'observer'),'--protocol=AODV','--arpDeadTimeout=3',f"--run={j['seed']}",f"--scenario={j['case']}",f"--fixture={j['case']}",f"--mainAt={j['mainAt']}",f"--mobility={P/'config'/(j['case']+'.csv')}",f'--out={prefix}','--diagnostic=1']
            start=time.monotonic()
            with Path(str(prefix)+'.log').open('w') as f:
                result=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60)
            record=dict(**j,exit_code=result.returncode,wall_s=time.monotonic()-start,command=command);records.append(record)
            Path(str(prefix)+'-status.json').write_text(json.dumps(record,indent=2)+'\n')
            print(key, 'exit', result.returncode, flush=True)
            if result.returncode: raise RuntimeError('Run failed; no automatic rerun')
    finally:
        (W/'COMPLETE.json').write_text(json.dumps(dict(results=records,total_completed=len(records),base_libraries_unchanged=all(sha(B/n)==h for n,h in build['reused_clean_non_aodv_libraries'].items())),indent=2)+'\n')
    assert len(records)==24
if __name__ == '__main__': main()
