# SPDX-License-Identifier: GPL-2.0-only
"""Reproduce the original-environment-1 delivery and request-localization example."""
from pathlib import Path
import argparse,csv,json,hashlib
P=Path(__file__).resolve().parent

def rd(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def wr(p,rows,fields):
    with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def analyze(root,out):
    root=root.resolve();out=out.resolve();assert out!=root and root not in out.parents
    if (root/'MANIFEST.json').exists():
        for e in json.loads((root/'MANIFEST.json').read_text())['files']:assert hashlib.sha256((root/e['path']).read_bytes()).hexdigest()==e['sha256']
    out.mkdir(parents=True,exist_ok=True);E={v:rd(root/f'original1-{v}-events.csv') for v in ['stock','patch']}
    tx={v:[(r['time'],r['flow'],r['seq'],r['bytes_or_send_result']) for r in rs if r['event']=='tx'] for v,rs in E.items()};assert tx['stock']==tx['patch'] and len(tx['stock'])==5985
    rx={v:{(int(r['flow']),int(r['seq'])):r for r in rs if r['event']=='rx' and r['unique_or_send_ok']=='1'} for v,rs in E.items()};ids={v:set(rs) for v,rs in rx.items()};assert [len(ids[v]) for v in ['stock','patch']]==[5854,5941]
    gained=ids['patch']-ids['stock'];lost=ids['stock']-ids['patch'];assert len(gained)==99 and len(lost)==12
    flow={v:{s for f,s in ss if f==1} for v,ss in ids.items()};assert [len(flow[v]) for v in ['stock','patch']]==[1099,1187]
    fg=flow['patch']-flow['stock'];fl=flow['stock']-flow['patch'];assert len(fg)==93 and len(fl)==5
    target_tx=[r for r in E['stock'] if r['flow']=='1' and r['event']=='tx'];assert len(target_tx)==1199
    cohort={int(r['seq']):r for r in target_tx if 106<=float(r['time'])<116};assert set(cohort)==set(range(459,559))
    counts={v:len(set(cohort)&flow[v]) for v in ['stock','patch']};assert counts=={'stock':7,'patch':99}
    rx_clock={v:len({int(r['seq']) for r in rs if r['flow']=='1' and r['event']=='rx' and r['unique_or_send_ok']=='1' and 106<=float(r['time'])<116}) for v,rs in E.items()};assert rx_clock=={'stock':4,'patch':99}
    assert all(float(r['time'])<=210 for rs in rx.values() for r in rs.values())
    rows=[]
    for seq,r in sorted(cohort.items()):
        rows.append({'flow':1,'sequence':seq,'generation_time_s':r['time'],'stock_received_by_210':seq in flow['stock'],'patch_received_by_210':seq in flow['patch'],'stock_reception_time_s':rx['stock'].get((1,seq),{}).get('time',''),'patch_reception_time_s':rx['patch'].get((1,seq),{}).get('time','')})
    wr(out/'generation_cohort_106_116.csv',rows,list(rows[0]))
    changes=[{'flow':f,'sequence':s,'change':'gained' if (f,s) in gained else 'lost'} for f,s in sorted(gained|lost)];wr(out/'delivery_changes.csv',changes,list(changes[0]))
    reasons=rd(root/'original1-stock-reasons.csv');guards=[r for r in reasons if r['origin']=='10.1.1.5' and r['destination']=='10.1.1.25' and r['request_id'] in ['4','5','6'] and r['reason']=='loop_guard_next_hop_equals_sender'];assert len(guards)==6
    assert {(int(r['node']),int(r['request_id'])) for r in guards}=={(n,k) for n in [3,8] for k in [4,5,6]}
    assert all(r['route_flag']=='1' and r['previous_ip']==r['next_hop'] and float(r['route_lifetime'])>0 for r in guards)
    first=next(r for r in guards if r['node']=='3' and r['request_id']=='4');assert abs(float(first['time'])-106.579200195)<1e-9 and abs(float(first['route_lifetime'])-9.939392525)<1e-9
    wr(out/'target_guard_drops.csv',guards,list(guards[0]))
    reqs=[]
    for v in ['stock','patch']:
        rs=[r for r in rd(root/f'original1-{v}-control-events.csv') if r['kind']=='RREQ' and r['origin']=='10.1.1.5' and r['destination']=='10.1.1.25' and r['event']=='TX' and r['node']=='4' and r['interface']!='0']
        assert rs[3]['request_id']=='4' and rs[3]['time']=='106.579'
        for r in rs:reqs.append({'variant':v,'time_s':r['time'],'request_id':r['request_id'],'ttl':r['ttl']})
    wr(out/'source_request_timeline.csv',reqs,list(reqs[0]))
    summary={'example':'Original 1 localization','all_flows_planned':5985,'all_flows_stock_received':5854,'all_flows_patch_received':5941,'all_flows_gained':99,'all_flows_lost':12,'all_flows_net':87,'target_flow':1,'target_source_node':4,'target_destination_node':24,'target_planned':1199,'target_stock_received':1099,'target_patch_received':1187,'target_gained':93,'target_lost':5,'target_net':88,'generation_window_s':[106,116],'generation_cohort_size':100,'generation_cohort_first_sequence':459,'generation_cohort_last_sequence':558,'observation_end_s':210,'generation_cohort_received_by_end':counts,'reception_clock_window_counts_not_the_reported_cohort':rx_clock,'fourth_source_rreq_time_s':106.579,'node3_guard_time_s':float(first['time']),'node3_invalid_retention_remaining_s':float(first['route_lifetime']),'interpretation':'The reported 7/99 compares final delivery of the same 100 packets generated in [106,116) s. It is not a count of receptions whose timestamps lie in that interval. Guard records expose the local mechanism; later network-wide gains/losses are not all attributed to that single event.'}
    (out/'localization_summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check-reference',action='store_true');a=p.parse_args();s=analyze(a.input,a.output)
    if a.check_reference:
        for ref in (P/'reference').iterdir():
            if ref.suffix in ['.csv','.json']:assert (a.output/ref.name).read_bytes()==ref.read_bytes(),ref.name
    print(json.dumps({'cohort':s['generation_cohort_size'],'delivered':s['generation_cohort_received_by_end'],'all_checks_passed':True},indent=2))
