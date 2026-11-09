#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Run the original failed wireless control and the one-time timing correction."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
P = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--ns3', type=Path, required=True); p.add_argument('--work', type=Path, required=True)
a = p.parse_args(); B=a.ns3.resolve(); W=a.work.resolve(); D=W/'build'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((W/'BUILD.json').read_text())
assert build['status']=='PASS' and not build['old_research_binaries_reused']
for prefix, field in [(D,'compiled_files'),(P,'research_sources'),(P,'configuration'),(B,'reused_clean_base_files')]:
    assert all(sha(prefix/name)==value for name,value in build[field].items()), 'Inputs changed after compilation: '+field
R=W/'runs'; R.mkdir(exist_ok=False); results=[]
config=json.loads((P/'configuration.json').read_text())
for j in json.loads((P/'cases.json').read_text()):
    out=R/j['name']
    env=dict(os.environ,LD_LIBRARY_PATH=str(D/'lib')+':'+str(B/'build/lib'),MANET_AODV_REASON_TRACE=str(out)+'-reason.csv')
    cmd=[str(D/j['harness']), '--protocol='+config['protocol'], '--arpDeadTimeout='+str(config['arp_dead_timeout_s']), '--run='+str(config['run']), '--scenario='+j['name'], '--mobility='+str(P/config['mobility']), '--out='+str(out), '--diagnostic='+str(config['diagnostic']), '--fixture='+config['fixture']]
    start=time.monotonic()
    with (R/(j['name']+'.log')).open('w') as log:
        r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    results.append(dict(name=j['name'],returncode=r.returncode,command=cmd,wall_seconds=time.monotonic()-start))
    (W/'RUNS.json').write_text(json.dumps(results,indent=2)+'\n')
    print(j['name'], 'PASS' if r.returncode==0 else 'FAIL',flush=True)
    if r.returncode:raise SystemExit(r.returncode)
assert len(results)==2
