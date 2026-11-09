#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic predicate tests, not additional network simulations."""
import argparse, csv, json, sys, tempfile
from pathlib import Path
P = Path(__file__).resolve().parent
sys.path.insert(0, str(P / 'analysis'))
from strict_returns import detect_returns
from analyze import cycles
p = argparse.ArgumentParser(description=__doc__); p.add_argument('--out', type=Path, required=True)
a = p.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
base = dict(node='0', ip_source='10.1.1.1', ip_destination='10.1.1.4', ip_protocol='17', ip_id='3', flow='1', seq='7', time='1', event='TX', interface='1', ttl='64', kind='DATA', packet_uid='42')
def tx(**kw): return dict(base, **kw)
def rx(**kw): return dict(base, **{'event':'RX','time':'2','ttl':'63',**kw})
tests = [
    ('strict_return', [tx(),rx()], 1,1),
    ('no_prior_tx', [rx()], 0,0),
    ('same_timestamp_not_earlier', [tx(),rx(time='1')], 0,0),
    ('ttl_equal', [tx(),rx(ttl='64')], 0,0),
    ('ttl_increased', [tx(),rx(ttl='65')], 0,0),
    ('tx_loopback', [tx(interface='0'),rx()], 0,0),
    ('rx_loopback', [tx(),rx(interface='0')], 0,0),
    ('different_node', [tx(),rx(node='1')], 0,0),
    ('different_ipv4_id', [tx(),rx(ip_id='4')], 0,0),
    ('different_app_seq', [tx(),rx(seq='8')], 0,0),
    ('different_flow', [tx(),rx(flow='2')], 0,0),
    ('different_destination', [tx(),rx(ip_destination='10.1.1.3')], 0,0),
    ('different_source', [tx(),rx(ip_source='10.1.1.5')], 0,0),
    ('different_protocol', [tx(),rx(ip_protocol='6')], 0,0),
    ('uid_auxiliary_only', [tx(),rx(packet_uid='99')], 1,1),
    ('two_returns_one_identity', [tx(),rx(),rx(time='3',ttl='62')], 1,2),
    ('general_forwarding_node', [tx(node='2',ip_source='10.1.1.5',flow='2'),rx(node='2',ip_source='10.1.1.5',flow='2')], 1,1),
    ('repeated_tx_is_not_return', [tx(),tx(time='2',ttl='63')], 0,0),
]
results = []
with tempfile.TemporaryDirectory(dir=a.out) as tmp:
    for name, rows, identities, events in tests:
        rows = [dict(r, order=str(i)) for i,r in enumerate(rows)]
        f = Path(tmp) / (name + '.csv')
        with f.open('w',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        r=detect_returns(f)
        assert r['any_node_identity_count'] == identities and r['matched_rx_event_count'] == events, name
        if name == 'general_forwarding_node': assert r['source_main_sequences'] == [] and r['other_node_or_flow_identity_count'] == 1
        results.append({'test':name,'passed':True})
    for name, edits in [('reject_nonmonotonic_order',{'order':'0'}),('reject_incomplete_identity',{'ip_id':''})]:
        rows=[dict(tx(),order='0'),dict(rx(),order='1')]; rows[-1].update(edits); f=Path(tmp)/(name+'.csv')
        with f.open('w',newline='') as stream:
            w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        try: detect_returns(f)
        except AssertionError: pass
        else: raise AssertionError(name)
        results.append({'test':name,'passed':True})

def state(edges, expiry='5', flag='0'):
    return [dict(snapshot='1',node=str(n),time='1',present=str(int(n in edges)),flag=flag,expiry=expiry,next_hop='10.1.1.'+str(edges.get(n,0)+1)) for n in range(4)]
for name, rows, stop, count, duration in [
    ('cycle_rotation_deduplication',state({0:1,1:0}),10,1,4),
    ('self_loop_excluded',state({0:0}),10,0,0),
    ('zero_lifetime_excluded',state({0:1,1:0},expiry='1'),10,0,0),
    ('invalid_routes_excluded',state({0:1,1:0},flag='1'),10,0,0),
    ('simulation_stop_bounds_cycle',state({0:1,1:0}),3,1,2),
    ('finite_graph_full_traversal',state({0:1,1:2,2:3,3:1}),10,1,4),
]:
    r=cycles(rows,stop); assert len(r)==count and sum(x['end']-x['start'] for x in r)==duration,name
    results.append({'test':name,'passed':True})
(a.out/'UNIT_TESTS.json').write_text(json.dumps({'passed':len(results),'network_simulations':0,'tests':results},indent=2)+'\n')
print('Passed',len(results),'synthetic analysis tests; no network simulations.')
