#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build fresh retention harnesses; optionally build a pinned ns-3.47 base first."""
import argparse, hashlib, json, os, shutil, subprocess, tarfile
from pathlib import Path
P = Path(__file__).resolve().parent
ARCHIVE_SHA = '8b3adca956c834ea436b915986ab8fd053e90041acae7426895d595aaa3ccc39'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def execute(command, cwd=None):
    subprocess.run([str(x) for x in command], cwd=cwd, check=True)
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--archive', type=Path, help='Official ns-3.47 tar.bz2; verifies SHA-256, extracts and builds inside --work')
    choice.add_argument('--ns3', type=Path, help='Existing clean, optimized ns-3.47 base to reuse')
    parser.add_argument('--work', type=Path, required=True, help='Private build output directory outside this candidate')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--cxx', default=os.environ.get('CXX', 'g++'))
    a = parser.parse_args(); W = a.work.resolve()
    if W == P or P in W.parents: parser.error('--work must be outside the public candidate')
    W.mkdir(parents=True, exist_ok=True)
    if (W/'build.json').exists(): parser.error('Use a fresh work directory; existing build.json is not overwritten')
    if a.archive:
        archive = a.archive.resolve(); assert sha(archive) == ARCHIVE_SHA, 'Archive SHA-256 mismatch'
        B = W/'base/ns-3.47'; B.parent.mkdir(exist_ok=True)
        with tarfile.open(archive) as tar: tar.extractall(B.parent, filter='data')
        execute(['./ns3', 'configure', '--build-profile=optimized', '--enable-modules=aodv,wifi,mobility,applications,flow-monitor,olsr,dsdv,dsr', '--disable-examples', '--disable-tests'], B)
        execute(['./ns3', 'build', '-j', a.jobs], B)
    else: B = a.ns3.resolve()
    expected = json.loads((P/'config/upstream_sources.json').read_text())
    assert (B/'VERSION').read_text().strip() == '3.47', 'Wrong ns-3 version'
    for path, digest in expected.items(): assert sha(B/path) == digest, 'Modified upstream source: '+path
    libs = sorted(x for x in (B/'build/lib').glob('libns3.47-*-optimized.so') if '-aodv-' not in x.name)
    assert libs, 'No optimized ns-3.47 libraries; configure/build the pinned base first'
    before = {str(x.relative_to(B)): sha(x) for x in libs}
    common = [a.cxx, '-O3', '-DNDEBUG', '-std=c++23', '-fPIC', '-I'+str(B/'build/include'), '-I'+str(B/'src/aodv/model'), '-DNS3_BUILD_PROFILE_OPTIMIZED']
    commands = []; objects = []; (W/'objects').mkdir(exist_ok=True)
    # Recompile all AODV translation units. Only non-AODV clean base libraries are reused.
    units = [('lifecycle', P/'sources/lifecycle-rtable.cc')]
    units += [(f.stem, f) for f in sorted((B/'src/aodv').rglob('*.cc')) if f.parent.name in ['model', 'helper'] and f.name not in ['aodv-routing-protocol.cc', 'aodv-rtable.cc']]
    for name, source in units:
        obj = W/'objects'/(name+'.o'); command = common+['-c', str(source), '-o', str(obj)]
        commands.append(command); execute(command); objects.append(str(obj))
    for version in ['stock', 'patch']:
        V = W/version; V.mkdir(exist_ok=True); obj = V/'routing.o'
        command = common+['-c', str(P/'sources'/(version+'-routing.cc')), '-o', str(obj)]
        commands.append(command); execute(command)
        command = [a.cxx, '-shared', '-Wl,-soname,libns3.47-aodv-optimized.so', '-o', str(V/'libns3.47-aodv-optimized.so'), str(obj)]+objects+['-Wl,-rpath,'+str(B/'build/lib')]+[str(x) for x in libs]
        commands.append(command); execute(command)
    command = common+[str(P/'sources/observer.cc'), '-o', str(W/'observer'), '-L'+str(W/'stock'), '-Wl,-rpath,'+str(B/'build/lib'), '-Wl,--no-as-needed', '-l:libns3.47-aodv-optimized.so']+[str(x) for x in libs]
    commands.append(command); execute(command)
    assert before == {str(x.relative_to(B)):sha(x) for x in libs}, 'Base libraries changed during compilation'
    manifest = dict(ns3=str(B),commands=commands,cxx=subprocess.check_output([a.cxx,'--version'],text=True).splitlines()[0],upstream_sources=expected,reused_clean_non_aodv_libraries=before,new_aodv_units=len(units)+2,research_sources={str(x.relative_to(P)):sha(x) for x in sorted((P/'sources').glob('*.cc'))},binaries={str(x.relative_to(W)):sha(x) for x in [W/'observer',W/'stock/libns3.47-aodv-optimized.so',W/'patch/libns3.47-aodv-optimized.so']})
    (W/'build.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS: fresh observer and both complete AODV libraries built; only clean non-AODV libraries reused.')
if __name__ == '__main__': main()
