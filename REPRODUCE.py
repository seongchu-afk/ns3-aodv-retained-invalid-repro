#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Unified corrective v2.0.1 analysis, bounded smoke, originals, and full workflows."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys

P = Path(__file__).resolve().parent
E = P / 'experiments'
O = P / 'original_cases'
PLAN = False


def run(script, *args):
    command = [sys.executable, str(script), *map(str, args)]
    print(shlex.join(command), flush=True)
    if not PLAN:
        subprocess.run(command, check=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))


def verify_manifest(root):
    data = json.loads((root / 'MANIFEST.json').read_text())
    for entry in data['files']:
        path = root / entry['path']
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], path


def separate_input_output(root, out):
    root, out = root.resolve(), out.resolve()
    assert root != out and root not in out.parents and out not in root.parents, 'Input and output trees must not overlap'


def strict_tests(out):
    target = out / 'strict_return_tests'
    if not PLAN:
        target.mkdir(parents=True, exist_ok=True)
        for name in ['strict_returns.py', 'test_strict_returns.py']:
            shutil.copyfile(P / 'analysis' / name, target / name)
    run(target / 'test_strict_returns.py')


def analyze_revision(root, out):
    separate_input_output(root, out)
    if not PLAN and (root / 'MANIFEST.json').exists():
        verify_manifest(root)
    strict_tests(out)
    run(P / 'analysis/analyze_temporal.py', '--input-root', root, '--output-root', out)
    target = out / 'ensemble'
    if not PLAN:
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / 'ENSEMBLE_COMPLETE.json', target / 'ENSEMBLE_COMPLETE.json')
        shutil.copyfile(E / 'analyze_ensemble.py', target / 'analyze_ensemble.py')
    run(target / 'analyze_ensemble.py')
    if PLAN:
        return
    actual = json.loads((out / 'TEMPORAL_EXTENDED.json').read_text())
    assert len(actual) == len({(x['suite'], x['case']) for x in actual}) == 195
    checks = {'temporal_cases': 195, 'ensemble_runs': 240, 'strict_predicate_tests': 15, 'reference_equal': {}}
    for name in ['TEMPORAL_EXTENDED.json', 'temporal_extended_summary.csv', 'counterexample_summary.csv', 'combined_summary.csv', 'recovery_windows.csv']:
        assert (out / name).read_bytes() == (P / 'reference' / name).read_bytes(), name
        checks['reference_equal'][name] = True
    for name in ['paired_runs.csv', 'ensemble_summary.csv', 'ensemble_summary.json']:
        assert (target / name).read_bytes() == (P / 'reference' / name).read_bytes(), name
        checks['reference_equal'][name] = True
    (out / 'VALIDATION.json').write_text(json.dumps(checks, indent=2) + '\n')


def analyze_added(root, out):
    separate_input_output(root, out)
    run(O / 'staged_table4/REPRODUCE.py', 'analysis', '--input', root / 'staged_table4', '--work', out / 'staged_table4')
    run(O / 'retention_figures/analyze.py', '--input', root / 'retention_figures', '--out', out / 'retention_figures', '--check-expected')
    run(O / 'valid_guard_control/REPRODUCE.py', 'analysis', '--input', root / 'valid_guard_control', '--work', out / 'valid_guard_control')
    for module, script in [('negative_chain', 'analyze_negative.py'), ('original1_localization', 'analyze_localization.py')]:
        run(O / module / script, '--input', root / module, '--output', out / module, '--check-reference')
    run(P / 'original_tables/supplementary_observer/verify.py', '--work', root / 'original_queue_observer', '--output', out / 'original_queue_observer')


def build_clean(archive, out, jobs):
    # Re-extract upstream and recompile research code; never reuse a simulation cache.
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = out / 'previous_experiments' / stamp
    names = ['ns-3.47', 'bin', 'stock', 'patch', 'temporal_lib', 'runs', 'temporal_runs', 'counterexample_runs', 'combined_runs', 'handler_checks']
    if not PLAN:
        existing = [E / name for name in names if (E / name).exists()]
        if existing:
            backup.mkdir(parents=True)
            for path in existing:
                shutil.move(path, backup / path.name)
    run(E / 'build.py', '--archive', archive, '--jobs', jobs)


def run_originals(out, jobs, reference=None):
    base = E / 'ns-3.47'
    work = out / 'original_tables'
    if not PLAN:
        assert not work.exists(), 'Use a fresh output directory for originals/full'
    run(P / 'original_tables/build.py', '--ns3', base, '--work', work, '--queue-observer')
    run(P / 'original_tables/run.py', '--ns3', base, '--work', work, '--jobs', jobs)
    run(P / 'original_tables/analyze.py', '--work', work)
    run(P / 'original_tables/supplementary_observer/verify.py', '--work', work, '--output', out / 'original_queue_observer')
    for module in ['staged_table4', 'valid_guard_control']:
        args = ['full', '--ns3', base, '--work', out / module]
        if reference:
            args += ['--reference-input', reference / module]
        run(O / module / 'REPRODUCE.py', *args)
    work_retention = out / 'retention_figures'
    run(O / 'retention_figures/build.py', '--ns3', base, '--work', work_retention, '--jobs', jobs)
    run(O / 'retention_figures/run.py', '--work', work_retention)
    args = ['--input', work_retention / 'runs', '--out', work_retention / 'analysis', '--check-expected']
    if reference:
        args += ['--reference-input', reference / 'retention_figures']
    run(O / 'retention_figures/analyze.py', *args)
    for module, script in [('negative_chain', 'analyze_negative.py'), ('original1_localization', 'analyze_localization.py')]:
        selected = out / 'selected_inputs' / module
        run(O / module / 'select_inputs.py', '--work', work, '--output', selected)
        run(O / module / script, '--input', selected, '--output', out / module, '--check-reference')


def handler_checks():
    run(E / 'run_handler_checks.py')
    if PLAN:
        return
    handlers = json.loads((E / 'HANDLER_COMPLETE.json').read_text())
    assert len(handlers) == 4 and all(x['exit_code'] == 0 for x in handlers)
    for ref in sorted((P / 'reference/handler_checks').glob('*.csv')):
        assert (E / 'handler_checks' / ref.name).read_bytes() == ref.read_bytes(), ref.name


def bounded_smoke(out):
    handler_checks()
    run(E / 'run_ensemble.py', '--smoke')
    run(E / 'smoke_fixtures.py')
    strict_tests(out)
    if PLAN:
        return
    expected = json.loads((P / 'reference/smoke_expected.json').read_text())
    rows = json.loads((E / 'SMOKE.json').read_text())['results']
    assert len(rows) == 2
    for row in rows:
        assert row['exit_code'] == 0
        for key, value in expected[row['version']].items():
            assert row[key] == value, ('ensemble smoke mismatch', row['version'], key)
    print('PASS: 12 handler CSVs, 20 ensemble values and five bounded fixture outcomes match the v2.0.0 references.')


def main(argv=None):
    global PLAN
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['analysis', 'smoke', 'originals', 'full'])
    parser.add_argument('--input', type=Path, help='Extracted analysis_data (analysis mode only)')
    parser.add_argument('--output', type=Path, default=P / 'results', help='Separate fresh output directory')
    parser.add_argument('--archive', type=Path, help='Official ns-3.47.tar.bz2 (simulation modes)')
    parser.add_argument('--reference-input', type=Path, help='Optional analysis_data for exact staged/retention/VALID CSV comparison in originals/full')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--plan', action='store_true', help='Print commands without writing, building or running simulations')
    args = parser.parse_args(argv)
    PLAN = args.plan
    out = args.output.resolve()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    if out == P or out in P.parents or out == E or E in out.parents:
        parser.error('--output cannot contain the code tree or overlap experiments/')
    if args.mode == 'analysis':
        if not args.input:
            parser.error('analysis requires --input pointing to extracted analysis_data')
        if args.archive or args.reference_input:
            parser.error('--archive and --reference-input are for simulation modes')
        root = args.input.resolve()
        separate_input_output(root, out)
    else:
        if not args.archive:
            parser.error('smoke/originals/full requires the official --archive')
        if args.input:
            parser.error('Simulation modes generate their own inputs; use --reference-input only for optional exact raw comparison')
        if args.reference_input and args.mode == 'smoke':
            parser.error('--reference-input is available for originals/full')
        if args.reference_input:
            args.reference_input = args.reference_input.resolve()
            separate_input_output(args.reference_input, out)
    if not PLAN:
        verify_manifest(P)
    if args.mode == 'analysis':
        verify = root / 'MANIFEST.json'
        if not PLAN:
            assert verify.is_file(), 'A complete versioned analysis_data manifest is required'
            verify_manifest(root)
        analyze_revision(root, out / 'revision')
        analyze_added(root, out)
    else:
        build_clean(args.archive.resolve(), out, args.jobs)
        if args.mode == 'smoke':
            bounded_smoke(out)
        else:
            if args.mode == 'full':
                handler_checks()
                for name in ['run_temporal.py', 'run_counterexample.py', 'run_combined.py', 'run_ensemble.py']:
                    run(E / name)
                analyze_revision(E, out / 'revision')
            run_originals(out, args.jobs, args.reference_input)
    run(P / 'analysis/validate_coverage.py', '--mode', args.mode, '--output', out)
    if not PLAN:
        print('PASS: corrective v2.0.1', args.mode, 'workflow. See COVERAGE_VALIDATION.json for the exact scope.')


if __name__ == '__main__':
    main()
