#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Check that missing or contradictory radio/handler evidence cannot qualify."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from analyze import load_traces, qualify, trace_directory
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input',type=Path,required=True)
args=parser.parse_args(); original=load_traces(trace_directory(args.input))
assert qualify(original)==json.loads((P/'expected/summary.json').read_text())
def rejection(label,mutate):
    traces=copy.deepcopy(original);mutate(traces)
    try:qualify(traces)
    except (ValueError,KeyError):print('PASS:',label)
    else:raise AssertionError('Accepted invalid evidence: '+label)
S='valid_negative_shifted'; I='valid_negative_patch'
def guard(traces):return next(r for r in traces[S]['reason'] if r['node']=='1' and r['request_id']=='9001')
rejection('INVALID is not a VALID guard',lambda t:guard(t).update(route_flag='1'))
rejection('Expired route is not live',lambda t:guard(t).update(route_lifetime='0'))
rejection('Wrong previous-hop predicate fails',lambda t:guard(t).update(previous_ip='10.1.1.3'))
rejection('Handler record without wireless RX fails',lambda t:t[S].update({'control-events':[r for r in t[S]['control-events'] if not (r['node']=='1' and r['event']=='RX' and r['request_id']=='9001')]}))
rejection('A different request identity fails',lambda t:guard(t).update(request_id='9002'))
def add_reply(t):
    row=copy.deepcopy(next(r for r in t[S]['control-events'] if r['node']=='1' and r['event']=='RX' and r['request_id']=='9001'))
    row.update(event='TX',kind='RREP',time='18.051');t[S]['control-events'].append(row)
rejection('RREP inside the no-reply window fails',add_reply)
def remove_overlap(t):
    row=next(r for r in t[I]['airtime'] if r['node']=='1' and r['time']=='18.00005' and r['kind']=='DATA')
    row['time']='18.001'
rejection('Initial half-duplex evidence is required',remove_overlap)
def remove_ppdu(t):t[S]['airtime']=[r for r in t[S]['airtime'] if not (r['node']=='0' and r['request_id']=='9001')]
rejection('Physical request PPDU is required',remove_ppdu)
provenance=json.loads((P/'PROVENANCE.json').read_text())
for source in provenance['source_files']:
    current=(P/source['path']).read_bytes()
    body=current.split(b' */\n',1)[1]
    assert hashlib.sha256(body).hexdigest()==source['original_sha256'],source['path']
    assert hashlib.sha256(current).hexdigest()==source['current_sha256'],source['path']
a=(P/'sources/observer.cc').read_text();b=(P/'sources/negative_shifted.cc').read_text()
assert a.count('Seconds(18),&InjectRequest')==1
assert a.replace('Seconds(18),&InjectRequest','Seconds(18.05),&InjectRequest')==b
print('PASS: original source bodies and injection-only difference preserved.')
print('PASS: baseline, eight rejected evidence mutations, and source integrity.')
