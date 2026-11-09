#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Portable analysis-only or complete 12-run staged Table 4 reproduction."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('mode', choices=['analysis','full'])
p.add_argument('--input', type=Path, help='External CSV directory or root containing traces/ (analysis only)')
p.add_argument('--reference-input', type=Path, help='Optional reference CSVs for exact byte comparison')
p.add_argument('--ns3', type=Path, help='Clean optimized ns-3.47 source/build tree (full only)')
p.add_argument('--work', type=Path, required=True, help='Fresh output directory, preferably under private_validation')
a = p.parse_args(); W = a.work.resolve()
for f in json.loads((P/'MANIFEST.json').read_text())['files']:
    path=P/f['path']; assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256'], f['path']
def run(name,*args): subprocess.run([sys.executable,str(P/name),*map(str,args)],check=True)
run('test_analysis.py','--out',W/'unit_tests')
if a.mode == 'full':
    if not a.ns3: p.error('full requires --ns3 pointing to the clean optimized ns-3.47 base')
    run('build.py','--ns3',a.ns3,'--work',W)
    run('run.py','--ns3',a.ns3,'--work',W)
    args = ['--input', W/'runs', '--out', W/'analysis']
else:
    args = ['--input', a.input or P/'reference/traces', '--out', W/'analysis']
if a.reference_input: args += ['--reference-input', a.reference_input]
run('analyze.py', *args)
