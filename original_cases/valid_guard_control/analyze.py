#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Trace-level qualification of the failed and corrected wireless VALID controls."""
import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path
P = Path(__file__).resolve().parent
D = Decimal
STEMS = ('valid_negative_patch', 'valid_negative_shifted')
KINDS = ('control-events', 'airtime', 'reason')
REQUIRED_TRACES = tuple(stem + '-' + kind + '.csv' for stem in STEMS for kind in KINDS)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def trace_directory(path):
    path = Path(path).resolve()
    return path / 'traces' if (path / 'traces').is_dir() else path


def read_rows(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def load_traces(path):
    return {name: {kind: read_rows(path / (name + '-' + kind + '.csv')) for kind in KINDS} for name in STEMS}


def matching_request(row):
    return row.get('request_id') == '9001' and row.get('origin') == '10.1.1.1' and row.get('destination') == '10.1.1.4'


def physical(row, node, event, kind):
    return row['node'] == str(node) and row['event'] == event and row['kind'] == kind and int(row['interface']) > 0


def qualify(traces):
    summaries = []
    for name, inject in zip(STEMS, ('18', '18.05')):
        data = traces[name]; control = data['control-events']; airtime = data['airtime']; reasons = data['reason']
        request_tx = [r for r in control if physical(r, 0, 'TX', 'RREQ') and matching_request(r)]
        require(len(request_tx) == 1, name + ': require exactly one physical request TX by S')
        tx = request_tx[0]
        require(D(tx['time']) == D(inject), name + ': wrong injection time')
        require(tx['ttl'] == '5' and tx['hop'] == '0' and tx['origin_seq'] == '100' and tx['destination_seq'] == '0' and tx['gratuitous'] == '0' and tx['destination_only'] == '0', name + ': wrong request header')
        ppdus = [r for r in airtime if r['node'] == '0' and r['kind'] == 'RREQ' and matching_request(r)]
        require(len(ppdus) == 1, name + ': require exactly one transmitted request PPDU')
        ppdu = ppdus[0]
        require(D(ppdu['time']) >= D(tx['time']) and int(ppdu['duration_ns']) > 0 and ppdu['group'] == '1', name + ': invalid request PPDU')
        d_rx = [r for r in control if physical(r, 3, 'RX', 'RREQ') and matching_request(r)]
        require(len(d_rx) == 1 and D(d_rx[0]['time']) > D(ppdu['time']), name + ': missing physical destination reception')
        b_rx = [r for r in control if physical(r, 1, 'RX', 'RREQ') and matching_request(r)]
        b_reason = [r for r in reasons if r['node'] == '1' and matching_request(r)]
        b_forward = [r for r in control if physical(r, 1, 'TX', 'RREQ') and matching_request(r)]
        start = D(inject); end = start + D('0.01')
        b_reply = [r for r in control if physical(r, 1, 'TX', 'RREP') and start <= D(r['time']) < end]
        # TX overlap is computed in exact decimal seconds. It establishes that B
        # is transmitting while S's request is on air; B cannot receive then.
        ppdu_end = D(ppdu['time']) + D(ppdu['duration_ns']) / D(1000000000)
        overlaps = [r for r in airtime if r['node'] == '1' and D(r['time']) < ppdu_end and D(r['time']) + D(r['duration_ns']) / D(1000000000) > D(ppdu['time'])]
        guard = None
        if name == STEMS[0]:
            require(not b_rx and not b_reason, 'Initial fixture must remain unqualified at B')
            require(any(r['kind'] == 'DATA' and r['flow'] == '0' and r['seq'] == '130' for r in overlaps), 'Initial half-duplex overlap evidence missing')
            qualification = False
        else:
            require(len(b_rx) == 1 and len(b_reason) == 1, 'Shifted request must reach B and have exactly one handler outcome')
            require(not overlaps, 'Shifted request must avoid B transmission overlap')
            rx = b_rx[0]; guard = b_reason[0]
            require(rx['packet_uid'] == tx['packet_uid'] and rx['ip_source'] == tx['ip_source'] and rx['ip_destination'] == tx['ip_destination'] and rx['ttl'] == tx['ttl'], 'TX/RX request identity mismatch')
            require(guard['time'] == rx['time'] and D(guard['time']) > D(ppdu['time']), 'Guard must follow actual wireless reception')
            require(guard['reason'] == 'loop_guard_next_hop_equals_sender' and guard['route_flag'] == '0', 'Guard did not reject a VALID route')
            require(guard['previous_ip'] == guard['next_hop'] == '10.1.1.1' and guard['hop'] == '1', 'Guard sender/next-hop predicate not satisfied')
            require(D(guard['route_lifetime']) > 0 and guard['valid_sequence'] == '1' and guard['route_sequence'] == '0' and guard['route_hops'] == '2', 'Wrong route state at VALID guard')
            require(not b_reply and not b_forward, 'B must neither reply nor forward the guarded request')
            qualification = True
        summaries.append(dict(name=name, injection_s=inject, qualified=qualification, request_tx_time=tx['time'], request_ppdu_time=ppdu['time'], request_ppdu_duration_ns=ppdu['duration_ns'], request_ppdu_end_s=str(ppdu_end), b_request_rx_count=len(b_rx), b_request_reason_count=len(b_reason), b_request_forward_count=len(b_forward), b_rrep_tx_count_in_10ms_window=len(b_reply), b_overlapping_ppdus=overlaps, valid_guard=guard))
    return summaries


def analyze(input_path, out_path, reference_path=None):
    source = trace_directory(input_path); out = Path(out_path).resolve()
    metadata = json.loads((P / 'PROVENANCE.json').read_text())
    filenames = [Path(r['path']).name for r in metadata['raw_files']]
    require(set(filenames) == set(REQUIRED_TRACES) and len(filenames) == 6, 'Invalid six-file scientific trace inventory')
    require(all((source / n).is_file() for n in filenames), 'Input must include all six required scientific CSV traces')
    result = qualify(load_traces(source))
    expected = json.loads((P / 'expected/summary.json').read_text())
    require(result == expected, 'Trace results differ from the small expected summary')
    hashes = {n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in filenames}
    comparison = None
    if reference_path is not None:
        ref = trace_directory(reference_path)
        require(all((ref/n).is_file() for n in filenames), 'Reference input is missing scientific traces')
        comparison = {n:hashes[n] == hashlib.sha256((ref/n).read_bytes()).hexdigest() for n in filenames}
        require(all(comparison.values()), 'Scientific traces differ from requested reference input')
    report = dict(status='PASS', summaries=result, input_trace_sha256=hashes, reference_byte_comparison=comparison, scientific_trace_count=6, limitation='One qualified wireless VALID-branch regression and its preceding unqualified fixture; not independent statistical samples or a proof of universal loop freedom.')
    out.mkdir(parents=True, exist_ok=False)
    (out/'ANALYSIS.json').write_text(json.dumps(report,indent=2)+'\n')
    with (out/'qualification.csv').open('w',newline='') as stream:
        fields=['name','injection_s','qualified','b_request_rx_count','b_request_reason_count','b_request_forward_count','b_rrep_tx_count_in_10ms_window']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in result)
    print('PASS: initial wireless fixture remains unqualified; shifted fixture reaches the VALID guard.')
    if comparison is not None:
        print('Reference byte equality: 6/6 required scientific traces.')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--reference-input',type=Path)
    args=parser.parse_args()
    analyze(args.input,args.out,args.reference_input)


if __name__=='__main__':
    main()
