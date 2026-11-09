#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Validate workflow reports and record numerical/event coverage without claiming figure redraws."""
import argparse
import json
from pathlib import Path
P = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['analysis','smoke','originals','full'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); out = args.output.resolve()
    index = json.loads((P/'MANUSCRIPT_COVERAGE.json').read_text())
    assert len([r for r in index['items'] if r['id'].startswith('F')]) == 6
    assert len([r for r in index['items'] if r['id'].startswith('T')]) == 7
    for item in index['items']:
        assert (P/item['reference']).is_file(), item['reference']
    reports = {}
    def read(name, path):
        reports[name] = path
        return json.loads((out/path).read_text())
    if args.mode in ['analysis','full']:
        report=read('revision','revision/VALIDATION.json')
        assert report['temporal_cases']==195 and report['ensemble_runs']==240
        assert len(report['reference_equal'])==8 and all(report['reference_equal'].values())
    if args.mode in ['analysis','originals','full']:
        staged=read('staged_table4','staged_table4/analysis/ANALYSIS.json')
        assert staged['case_count']==12 and staged['table4_matches']
        retention_path='retention_figures/'+('' if args.mode=='analysis' else 'analysis/')+'validation.json'
        retention=read('retention_figures',retention_path)
        assert retention['total_runs']==24 and retention['pass_all']
        valid=read('valid_guard_control','valid_guard_control/analysis/ANALYSIS.json')
        assert valid['status']=='PASS' and valid['scientific_trace_count']==6
        read('negative_chain','negative_chain/negative_summary.json')
        read('original1_localization','original1_localization/localization_summary.json')
        queue=read('original_queue_observer','original_queue_observer/NEW_QUEUE_OBSERVER_VALIDATION.json')
        assert queue['pass'] and queue['fifo_evictions']==31 and queue['retry_exhaustion_drops']==64
    if args.mode in ['originals','full']:
        original=read('original_tables','original_tables/VALIDATION.json')
        assert original['S1_cases_checked']==198 and original['S4_six_environments_match'] is True
    if args.mode=='smoke':
        tests=read('strict_return_tests','strict_return_tests/ANALYSIS_UNIT_TESTS.json')
        assert len(tests)==15 and all(r['passed'] for r in tests)
    rows=[]
    for item in index['items']:
        module=item['module']
        status='reference_present_only'
        if module in reports:
            status='archived_numeric_evidence_checked' if args.mode=='analysis' else 'fresh_generated_evidence_checked'
        if module=='configuration':status='configuration_reference_present'
        rows.append(dict(item,status=status,report=reports.get(module)))
    result={'version':'2.0.1','mode':args.mode,'pass':True,'figure_entries':6,'table_entries':7,'narrative_entries':2,
            'coverage_kind':index['coverage_kind'],'reports':reports,'items':rows,
            'fresh_revision_435_simulations':args.mode=='full','fresh_original_simulations':args.mode in ['originals','full'],
            'historical_queue_observer_recovered':False,'new_queue_observer_evidence_checked':'original_queue_observer' in reports,
            'limitations':['Reference presence is not a fresh simulation result.','No publication-layout figure redraw is claimed.','Historical direct queue source and trace remain unrecovered.']}
    out.mkdir(parents=True,exist_ok=True)
    (out/'COVERAGE_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Coverage validated:',args.mode,'6 figures, 7 tables, 2 narrative entries; exact statuses in COVERAGE_VALIDATION.json')
if __name__=='__main__':main()
