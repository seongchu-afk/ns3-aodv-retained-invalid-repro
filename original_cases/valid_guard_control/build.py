#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Freshly compile the wireless control module against a clean ns-3.47 build."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
P = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--ns3', type=Path, required=True)
p.add_argument('--work', type=Path, required=True)
p.add_argument('--cxx', default=os.environ.get('CXX', 'g++'))
a = p.parse_args(); B = a.ns3.resolve(); W = a.work.resolve(); S = P / 'sources'
assert (B / 'VERSION').read_text().strip() == '3.47'
expected = {'aodv-routing-protocol.cc':'43b8ff9e5ccd4c737422de1ebb191c1913cdfb33259c1bb2dab6d9720d77c79e','aodv-rtable.cc':'249c194a3115b62ea9798316ec78a7dc3eea644894d80b63361d2da1f2c28ed7'}
for name, digest in expected.items():
    assert sha(B / 'src/aodv/model' / name) == digest, 'Clean upstream source required: ' + name
original = (S / 'observer.cc').read_text()
assert original.count('Seconds(18),&InjectRequest') == 1
assert original.replace('Seconds(18),&InjectRequest', 'Seconds(18.05),&InjectRequest') == (S / 'negative_shifted.cc').read_text(), 'Only injection time may differ'
libs = sorted(x for x in (B / 'build/lib').glob('*.so') if 'aodv' not in x.name)
objs = sorted(x for x in (B / 'cmake-cache/src/aodv').rglob('*.o') if x.name != 'aodv-routing-protocol.cc.o')
assert libs and len(objs) == 7, 'An optimized ns-3.47 base build is required'
D = W / 'build'; assert not D.exists(), 'Use a fresh work directory'
D.mkdir(parents=True); L = D / 'lib'; L.mkdir()
base = [a.cxx, '-O3', '-DNDEBUG', '-std=c++23', '-fPIC', '-I' + str(B / 'build/include'), '-I' + str(B / 'src/aodv/model'), '-DNS3_BUILD_PROFILE_OPTIMIZED']
commands = [base + ['-c', str(S / 'patch-routing.cc'), '-o', str(D / 'routing.o')]]
commands.append([a.cxx, '-shared', '-Wl,-soname,libns3.47-aodv-optimized.so', '-o', str(L / 'libns3.47-aodv-optimized.so'), str(D / 'routing.o')] + list(map(str, objs)) + ['-Wl,-rpath,' + str(B / 'build/lib')] + list(map(str, libs)))
for name in ['observer', 'negative_shifted']:
    commands.append(base + [str(S / (name + '.cc')), '-o', str(D / name), '-L' + str(L), '-Wl,-rpath,' + str(B / 'build/lib'), '-Wl,--no-as-needed', '-l:libns3.47-aodv-optimized.so'] + list(map(str, libs)))
record = dict(ns3=str(B), commands=commands, compiler=subprocess.check_output([a.cxx, '--version'], text=True).splitlines()[0], old_research_binaries_reused=False, reused_clean_base_files={str(x.relative_to(B)):sha(x) for x in objs + libs}, research_sources={str(x.relative_to(P)):sha(x) for x in S.iterdir() if x.is_file()}, configuration={n:sha(P/n) for n in ['cases.json','configuration.json','mobility/negative.csv']})
(W / 'BUILD.json').write_text(json.dumps(record, indent=2) + '\n')
start = time.monotonic()
with (W / 'build.log').open('w') as log:
    for i, cmd in enumerate(commands, 1):
        print(f'Compiling wireless control: {i}/{len(commands)}', flush=True)
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
record.update(status='PASS', wall_seconds=time.monotonic()-start, compiled_files={str(x.relative_to(D)):sha(x) for x in D.rglob('*') if x.is_file()})
(W / 'BUILD.json').write_text(json.dumps(record, indent=2) + '\n')
print('Routing module and both harnesses freshly compiled.')
