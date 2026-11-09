#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Execute the complete fixed 12-case staged matrix with freshly compiled harnesses."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
P = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--ns3', type=Path, required=True); p.add_argument('--work', type=Path, required=True)
a = p.parse_args(); B = a.ns3.resolve(); W = a.work.resolve(); D = W / 'build'
build = json.loads((W / 'BUILD.json').read_text())
assert build['status'] == 'PASS' and not build['old_research_binaries_reused']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(D / name) == value for name, value in build['compiled_files'].items())
assert all(sha(P / name) == value for name, value in build['research_sources'].items()), 'Source changed after compilation'
assert all(sha(B / name) == value for name, value in build['reused_clean_base_files'].items()), 'Base changed after compilation'
R = W / 'runs'; R.mkdir(exist_ok=False); results = []
for j in json.loads((P / 'cases.json').read_text()):
    name = j['case'] + '-' + j['version']; out = R / name
    env = dict(os.environ, LD_LIBRARY_PATH=str(D / j['version']) + ':' + str(B / 'build/lib'), MANET_AODV_REASON_TRACE=str(out) + '-reason.csv', MANET_AODV_LIFECYCLE_TRACE=str(out) + '-lifecycle.csv')
    cmd = [str(D / j['harness']), '--protocol=AODV', '--fixture=' + j['fixture'], '--mobility=' + str(P / 'mobility' / j['mobility']), '--out=' + str(out), '--run=' + str(j['run']), '--arpDeadTimeout=' + str(j['arp_dead_timeout_s']), '--hello=' + str(j['hello']), '--mainAt=' + j['main_at']]
    start = time.monotonic()
    with (R / (name + '.log')).open('w') as log:
        r = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    results.append({'case': j['case'], 'version': j['version'], 'returncode': r.returncode, 'wall_seconds': time.monotonic() - start, 'command': cmd})
    (W / 'RUNS.json').write_text(json.dumps(results, indent=2) + '\n')
    print(name, 'PASS' if r.returncode == 0 else 'FAIL', flush=True)
    if r.returncode: raise SystemExit(r.returncode)
assert len(results) == 12
print('Completed all 12 staged simulations.')
