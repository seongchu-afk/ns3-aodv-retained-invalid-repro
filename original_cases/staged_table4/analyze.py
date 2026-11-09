#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Recompute Table 4, qualification and strict packet-return evidence from raw CSVs."""
import argparse, collections, csv, hashlib, json, math, sys
from decimal import Decimal
from pathlib import Path
P = Path(__file__).resolve().parent
sys.path.insert(0, str(P / 'analysis'))
from strict_returns import detect_returns
IDENTITY = ('ip_source', 'ip_destination', 'ip_protocol', 'ip_id', 'flow', 'seq')

def read(path):
    with path.open(newline='') as f: return list(csv.DictReader(f))

def write_csv(path, rows, fields=None):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0])); w.writeheader(); w.writerows(rows)

def cycles(snapshots, stop):
    groups = collections.defaultdict(list)
    for row in snapshots: groups[int(row['snapshot'])].append(row)
    ids = sorted(groups); intervals = []
    for i, sid in enumerate(ids):
        rows = groups[sid]
        assert len(rows) == 4 and {r['node'] for r in rows} == {'0','1','2','3'}
        t = float(rows[0]['time']); assert all(float(r['time']) == t for r in rows)
        end = min(stop, float(groups[ids[i + 1]][0]['time']) if i + 1 < len(ids) else stop)
        assert end >= t
        live = {int(r['node']): r for r in rows if r['present'] == '1' and r['flag'] == '0' and float(r['expiry']) > t}
        edges = {n: int(r['next_hop'].split('.')[-1]) - 1 for n, r in live.items()}
        found = set()
        for start in edges:
            path = []; node = start
            while node in edges:
                if node in path:
                    cycle = path[path.index(node):]
                    if len(cycle) > 1:
                        key = min(tuple(cycle[j:] + cycle[:j]) for j in range(len(cycle)))
                        if key not in found:
                            found.add(key)
                            until = min(end, *[float(live[n]['expiry']) for n in cycle])
                            intervals.append({'snapshot': sid, 'start': t, 'end': max(t, until), 'cycle': list(key)})
                    break
                path.append(node); node = edges[node]
    return intervals

def qualify(case, version, config, rows):
    reason, life, snap, events, q = (rows[k] for k in ['reason','lifecycle','route-snapshots','events','qualification'])
    hits = [r for r in reason if r['node'] == '1' and r['previous_ip'] == '10.1.1.1' and r['origin'] == '10.1.1.1' and r['destination'] == '10.1.1.4' and float(r['time']) >= float(config['main_at']) and r['reason'] == 'destination_route_present']
    first = hits[0] if hits else None
    b = [r for r in life if r['owner_ip'] == '10.1.1.2' and r['destination'] == '10.1.1.4']
    invalid = [r for r in b if r['action'].endswith('after_invalidate')]
    prior = [r for r in invalid if first and float(r['time']) <= float(first['time'])]
    last = prior[-1] if prior else None
    detail = {'case':case, 'version':version, 'first_main_B_request_state':first, 'prior_invalidation':last}
    if case == 'P':
        source = [r for r in snap if Decimal(r['time']) == Decimal('9.1') and r['node'] == '0']
        bstate = [r for r in snap if Decimal(r['time']) == Decimal('9.1') and r['node'] == '1']
        assert len(source) >= 2
        pre, post = source[0], source[1]
        unchanged = all(pre[k] == post[k] for k in ['valid_seq','seq','next_hop','hops'])
        passed = bool(q) and all(r['pass'] == '1' for r in q) and first is not None and first['route_flag'] == '0' and first['next_hop'] == '10.1.1.1' and float(first['route_lifetime']) > 0
        passed = passed and pre['flag'] == '0' and post['flag'] == '1' and unchanged and all(r['flag'] == '0' for r in bstate)
        detail.update(perturbation={'before':pre,'after':post,'unchanged_sequence_next_hop_hops':unchanged,'B_states':bstate}, precondition_rows=q)
    else:
        passed = first is not None and first['route_flag'] == '1' and last is not None and last['action'] == ('rerr_after_invalidate' if case == 'L' else 'purge_after_invalidate')
    if case == 'E':
        # Preserve the failed intended-expiry condition. A later recovery/cycle is not a pass.
        detail['B_RERR_invalidations'] = [r for r in invalid if r['action'] == 'rerr_after_invalidate']
        detail['intended_expiry_qualification'] = 'failed' if not passed else 'passed'
    if case == 'E2':
        early = [r for r in invalid if float(r['time']) < 20]
        inv = early[0] if early else None
        history = [r for r in snap if r['node'] == '1' and inv and first and float(inv['time']) <= float(r['time']) <= float(first['time'])]
        continuous = bool(history) and all(r['present'] == '1' and r['flag'] == '1' and r['next_hop'] == '10.1.1.1' and r['seq'] == inv['sequence'] for r in history)
        earlier_rerr = [r for r in life if r['destination'] == '10.1.1.4' and 'rerr_' in r['action'] and inv and float(r['time']) <= float(inv['time'])]
        control_rerr = [r for r in rows['control-events'] if r['kind'] == 'RERR' and '10.1.1.4:' in r['unreachable']]
        prior_control_rerr = [r for r in control_rerr if inv and Decimal(r['time']) <= Decimal(inv['time'])]
        warm = {r['seq'] for r in events if r['flow'] == '0' and r['event'] == 'rx' and inv and float(r['time']) < float(inv['time'])}
        deleted = [r for r in b if r['action'] == 'purge_delete_invalid' and inv and first and float(inv['time']) < float(r['time']) < float(first['time'])]
        passed = passed and inv is not None and inv['action'] == 'purge_after_invalidate' and continuous and not earlier_rerr and not prior_control_rerr and not deleted and len(warm) == 40
        detail.update(target_RERR_control_events=control_rerr, target_RERR_control_events_before_invalidation=prior_control_rerr, first_invalidation=inv, continuous_same_entry_snapshots=len(history), strictly_before_request_snapshots=sum(float(r['time']) < float(first['time']) for r in history) if first else 0, continuous_INVALID_same_next_seq=continuous, earlier_target_RERR_events=earlier_rerr, deleted_invalid_entries=deleted, warm_received_before_invalidation=len(warm), all_target_RERR_lifecycle_events=[r for r in life if r['destination'] == '10.1.1.4' and 'rerr_' in r['action']])
    detail['qualified'] = bool(passed)
    return detail

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', '--runs', dest='runs', type=Path, default=P / 'reference/traces', help='Directory containing the case CSVs, or a data root containing traces/')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--reference-input', type=Path, help='Optional original CSV directory for byte-level comparison')
    p.add_argument('--compare-reference-traces', action='store_true', help='Use bundled reference/traces when no --reference-input is supplied')
    a = p.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    if (a.runs / 'traces').is_dir(): a.runs = a.runs / 'traces'
    if not a.runs.is_dir(): p.error('Supply --input pointing to the extracted staged Table 4 CSV data.')
    reference_input = a.reference_input or (P / 'reference/traces' if a.compare_reference_traces else None)
    if reference_input is not None and (reference_input / 'traces').is_dir(): reference_input = reference_input / 'traces'
    if reference_input is not None:
        if not reference_input.is_dir(): p.error('--reference-input must contain the reference CSV files.')
        required_names = {j['case'] + '-' + j['version'] + '-' + k + '.csv' for j in json.loads((P / 'cases.json').read_text()) for k in ['events','flows','control-events','route-snapshots','lifecycle','reason','qualification','graph']}
        missing = sorted(name for name in required_names if not (reference_input / name).is_file())
        if missing: p.error('Missing reference CSVs: ' + ', '.join(missing))
    result = []; details = {}; parity = []
    expected = {(r['case'], r['version']):r for r in read(P / 'reference/Table4_expected.csv')}
    historical = {(r['case'], r['version']):r for r in read(P / 'reference/historical_SUMMARY.csv')}
    checks = []
    for config in json.loads((P / 'cases.json').read_text()):
        case, version = config['case'], config['version']; name = case + '-' + version
        rows = {k:read(a.runs / (name + '-' + k + '.csv')) for k in ['events','flows','control-events','route-snapshots','lifecycle','reason','qualification','graph']}
        flows = rows['flows']; main_flow = next(r for r in flows if r['flow'] == '1')
        app_tx = [r for r in rows['events'] if r['flow'] == '1' and r['event'] == 'tx']
        app_rx = {r['seq'] for r in rows['events'] if r['flow'] == '1' and r['event'] == 'rx'}
        planned, received = int(main_flow['planned']), int(main_flow['unique_received'])
        assert planned == len(app_tx) == config['planned'] and received == len(app_rx), name + ': inconsistent application ledger'
        intervals = cycles(rows['route-snapshots'], config['stop_s'])
        strict = detect_returns(a.runs / (name + '-control-events.csv'), a.out / (name + '-strict-return-pairs.csv'))
        pairs = read(a.out / (name + '-strict-return-pairs.csv'))
        returned_datagrams = {tuple(r[k] for k in IDENTITY) for r in pairs}
        tx_counts = collections.Counter((tuple(r[k] for k in IDENTITY), r['node']) for r in rows['control-events'] if r['kind'] == 'DATA' and r['event'] == 'TX' and r['interface'] != '0')
        repeated = {key for (key,node), count in tx_counts.items() if count > 1}
        q = qualify(case, version, config, rows)
        row = {'case':case,'version':version,'planned':planned,'received':received,'qualified':q['qualified'],'active_cycle_intervals':len(intervals),'active_cycle_duration_s':sum(r['end']-r['start'] for r in intervals),'strict_returned_datagrams':len(returned_datagrams),'strict_source_main_sequences':len(strict['source_main_sequences']),'repeated_physical_tx_datagrams':len(repeated)}
        target = expected[(case,version)]
        for k, value in row.items():
            if k == 'active_cycle_duration_s': ok = math.isclose(value, float(target[k]), abs_tol=1e-9, rel_tol=0)
            else: ok = str(value) == target[k]
            checks.append({'case':case,'version':version,'field':k,'matches':ok})
        old = historical[(case,version)]
        assert int(old['packets_returning_to_prior_tx_node']) == len(returned_datagrams), name + ': historical versus strict return mismatch'
        result.append(row); details[name] = {'cycles':intervals,'qualification':q,'strict_returns':strict,'historical_strict_return_count':int(old['packets_returning_to_prior_tx_node']), 'strict_returned_datagram_identities':[list(k) for k in sorted(returned_datagrams)],'repeated_physical_TX_identities':[list(k) for k in sorted(repeated)]}
        if reference_input is not None:
            for ref in sorted(reference_input / f for f in required_names if f.startswith(name + '-')):
                actual = a.runs / ref.name
                hashfile = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()
                parity.append({'file':ref.name,'reference_sha256':hashfile(ref),'rerun_sha256':hashfile(actual),'byte_identical':ref.read_bytes()==actual.read_bytes()})
    assert len(result) == 12
    report = {'case_count':len(result),'table4_matches':all(r['matches'] for r in checks),'field_checks':checks,'trace_count':len(parity),'all_reference_traces_byte_identical':all(r['byte_identical'] for r in parity) if parity else None,'trace_checks':parity,'cases':details}
    write_csv(a.out / 'Table4_recomputed.csv', result)
    (a.out / 'ANALYSIS.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if not report['table4_matches'] or (parity and not report['all_reference_traces_byte_identical']): raise SystemExit('Mismatch: inspect ANALYSIS.json; no reference data were changed.')
    print('All 12 Table 4 cases match; qualifications and strict return identities verified.')
if __name__ == '__main__': main()
