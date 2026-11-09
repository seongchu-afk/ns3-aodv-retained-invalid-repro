#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Compile every staged harness and variant, reusing only a clean ns-3.47 base."""
import argparse, hashlib, json, os, subprocess, time
from pathlib import Path
P = Path(__file__).resolve().parent
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--ns3', type=Path, required=True)
p.add_argument('--work', type=Path, required=True)
p.add_argument('--cxx', default=os.environ.get('CXX', 'g++'))
a = p.parse_args(); B = a.ns3.resolve(); W = a.work.resolve(); S = P / 'sources'
assert (B / 'VERSION').read_text().strip() == '3.47'
expected = {'aodv-routing-protocol.cc': '43b8ff9e5ccd4c737422de1ebb191c1913cdfb33259c1bb2dab6d9720d77c79e', 'aodv-rtable.cc': '249c194a3115b62ea9798316ec78a7dc3eea644894d80b63361d2da1f2c28ed7'}
for name, digest in expected.items():
    assert SHA(B / 'src/aodv/model' / name) == digest, 'Clean upstream source required: ' + name
libs = sorted(x for x in (B / 'build/lib').glob('*.so') if 'aodv' not in x.name)
objs = sorted(x for x in (B / 'cmake-cache/src/aodv').rglob('*.o') if x.name not in {'aodv-routing-protocol.cc.o', 'aodv-rtable.cc.o'})
assert libs and len(objs) == 6, 'Build the pinned optimized ns-3.47 base with CMake/Unix Makefiles first.'
assert not (W / 'build').exists(), 'Use a fresh work directory; old research binaries are never reused.'
D = W / 'build'; D.mkdir(parents=True); commands = []
base = [a.cxx, '-O3', '-DNDEBUG', '-std=c++23', '-fPIC', '-I' + str(S), '-I' + str(B / 'build/include'), '-I' + str(B / 'src/aodv/model'), '-DNS3_BUILD_PROFILE_OPTIMIZED']
commands.append(base + ['-c', str(S / 'lifecycle-rtable.cc'), '-o', str(D / 'lifecycle.o')])
for version in ['stock', 'patch', 'unsafe']:
    V = D / version; V.mkdir()
    commands.append(base + ['-c', str(S / (version + '-routing.cc')), '-o', str(V / 'routing.o')])
    commands.append([a.cxx, '-shared', '-o', str(V / 'libns3.47-aodv-optimized.so'), str(V / 'routing.o'), str(D / 'lifecycle.o')] + list(map(str, objs)) + ['-Wl,-rpath,' + str(B / 'build/lib')] + list(map(str, libs)))
for name in ['observer', 'expiry-observer']:
    commands.append(base + [str(S / (name + '.cc')), '-o', str(D / name), '-L' + str(D / 'stock'), '-Wl,-rpath,' + str(B / 'build/lib'), '-Wl,--no-as-needed', '-l:libns3.47-aodv-optimized.so'] + list(map(str, libs)))
record = {'ns3': str(B), 'commands': commands, 'compiler': subprocess.check_output([a.cxx, '--version'], text=True).splitlines()[0], 'reused_clean_base_files': {str(x.relative_to(B)): SHA(x) for x in objs + libs}, 'research_sources': {str(x.relative_to(P)): SHA(x) for x in S.iterdir() if x.is_file()}, 'old_research_binaries_reused': False}
(W / 'BUILD.json').write_text(json.dumps(record, indent=2) + '\n')
start = time.monotonic()
with (W / 'build.log').open('w') as log:
    for i, cmd in enumerate(commands, 1):
        print(f'Compiling staged module: {i}/{len(commands)}', flush=True)
        subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
record.update(wall_seconds=time.monotonic() - start, status='PASS', compiled_files={str(x.relative_to(D)): SHA(x) for x in D.rglob('*') if x.is_file()})
(W / 'BUILD.json').write_text(json.dumps(record, indent=2) + '\n')
print('All staged variants and both harnesses newly compiled.')
