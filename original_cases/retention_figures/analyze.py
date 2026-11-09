#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Recompute original metrics and verify every fixed case plus Figure 2/3 data."""
from pathlib import Path
import argparse, csv, json, collections, hashlib
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input','--runs',dest='input',type=Path,required=True,help='External data root containing runs/, or a direct CSV directory (--runs is a compatibility alias)')
parser.add_argument('--reference-input',type=Path,help='Optional external original-data root or direct CSV directory for explicit byte comparison')
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--check-expected',action='store_true')
a=parser.parse_args()
def resolve_runs(root):
    root=root.resolve()
    return root/'runs' if (root/'runs').is_dir() else root
runs=resolve_runs(a.input);reference_runs=resolve_runs(a.reference_input) if a.reference_input else None;output=a.out.resolve()
if output==P or P in output.parents: parser.error('--out must be outside the public candidate')
output.mkdir(parents=True,exist_ok=True)
read=lambda p:list(csv.DictReader(open(p))) if Path(p).exists() else []
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# The original round16 analysis expressions below are unchanged, except input/output paths.
freeze=json.loads((P/'config/matrix.json').read_text());rows=[];pairs=[]
for j in freeze['jobs']:
 key=f"{j['case']}-{j['seed']}-{j['version']}";pre=runs/key;e=read(str(pre)+'-events.csv');r=read(str(pre)+'-reason.csv');life=read(str(pre)+'-lifecycle.csv');ctrl=read(str(pre)+'-control-events.csv');air=read(str(pre)+'-airtime.csv');tx=[x for x in e if x['flow']=='1' and x['event']=='tx'];rx=[x for x in e if x['flow']=='1' and x['event']=='rx' and x['unique_or_send_ok']=='1'];lookup=[x for x in r if float(x['time'])>=j['mainAt'] and x['node']=='1' and x['origin']=='10.1.1.1' and x['destination']=='10.1.1.4' and x['reason'] in ['destination_route_present','destination_route_absent']];first=lookup[0] if lookup else None
 expected='INVALID' if j['case'] in ['retained','second'] else 'ABSENT';actual='UNKNOWN' if not first else 'ABSENT' if first['reason']=='destination_route_absent' else {'0':'VALID','1':'INVALID','2':'IN_SEARCH'}.get(first['route_flag'],'OTHER')
 row=dict(**j,planned=len(tx),accepted=sum(x['unique_or_send_ok']=='1' for x in tx),received_final=len(rx),received_1s=sum(float(x['time'])<=j['mainAt']+1 for x in rx),received_5s=sum(float(x['time'])<=j['mainAt']+5 for x in rx),first_rx_wait_s=min((float(x['time'])-j['mainAt'] for x in rx),default=None),expected_B_state=expected,actual_B_state=actual,state_qualification=actual==expected,first_B_lookup=first,B_D_lifecycle=[x for x in life if x['owner_ip']=='10.1.1.2' and x['destination']=='10.1.1.4'],RREQ_main_attempts=len({x['request_id'] for x in ctrl if x['kind']=='RREQ' and x['event']=='TX' and x['node']=='0' and x['interface']=='1' and float(x['time'])>=j['mainAt']}),control_tx_duration_ns=sum(int(x['duration_ns']) for x in air if x['kind'] in ['RREQ','RREP','HELLO','RERR','RREP_ACK'] and float(x['time'])>=j['mainAt']))
 row["discovery_control_tx_duration_ns"]=sum(int(x["duration_ns"]) for x in air if x["kind"] in ["RREQ","RREP","RERR","RREP_ACK"] and float(x["time"])>=j["mainAt"])
 row["seq0_received_final"]=any(x["seq"]=="0" for x in rx)
 row["seq0_received_1s"]=any(x["seq"]=="0" and float(x["time"])<=j["mainAt"]+1 for x in rx)
 row["seq0_received_5s"]=any(x["seq"]=="0" and float(x["time"])<=j["mainAt"]+5 for x in rx)
 rows.append(row)
for c in ['retained','after_delete','cold','second']:
 for seed in [1,2,3]:
  versions={v:read(str(runs/f'{c}-{seed}-{v}')+'-control-events.csv') for v in ['stock','patch']};at=next(j['mainAt'] for j in freeze['jobs'] if j['case']==c);before={v:[x for x in r if float(x['time'])<at] for v,r in versions.items()};pairs.append(dict(case=c,seed=seed,pre_main_control_exact_equal=before['stock']==before['patch'],prefix_rows=len(before['stock'])))
(output/'SUMMARY.json').write_text(json.dumps(dict(rows=rows,pairs=pairs,limits=['4 packets within seed not independent replications','stage qualifications actual not assumed','sim60 undelivered is right-censored observation, not forever loss']),indent=2))
fields=[x for x in rows[0] if x not in ['first_B_lookup','B_D_lifecycle','command']]
with (output/'matrix.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in rows)
print(json.dumps([{k:r[k] for k in ['case','seed','version','planned','received_final','received_1s','received_5s','actual_B_state','state_qualification']} for r in rows],indent=2))
# Additional qualification, exact-reproduction and figure-data checks.
def write_csv(path, records):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
checks=[];timeline=[];delivery=[];prefixes=[];timings=[]
for j,row in zip(freeze['jobs'],rows):
    key=f"{j['case']}-{j['seed']}-{j['version']}";pre=runs/key;at=j['mainAt']
    events=read(str(pre)+'-events.csv');reasons=read(str(pre)+'-reason.csv');life=read(str(pre)+'-lifecycle.csv')
    tx=[r for r in events if r['flow']=='1' and r['event']=='tx'];rx=[r for r in events if r['flow']=='1' and r['event']=='rx' and r['unique_or_send_ok']=='1']
    first=row['first_B_lookup'];bl=[r for r in life if r['owner_ip']=='10.1.1.2' and r['destination']=='10.1.1.4']
    initial_invalid=next((r for r in bl if r['action'].endswith('after_invalidate') and float(r['time'])<at),None)
    initial_delete=next((r for r in bl if r['action']=='purge_delete_invalid'),None)
    scheduled=(len(tx)==4 and {r['seq'] for r in tx}=={'0','1','2','3'} and all(abs(float(r['time'])-at-0.1*int(r['seq']))<1e-9 for r in tx))
    retained=j['case'] in ['retained','second']
    state_ok=bool(first) and row['state_qualification']
    if retained: state_ok=state_ok and first['next_hop']==first['previous_ip']=='10.1.1.1' and float(first['route_lifetime'])>0 and bool(initial_invalid) and not any(r['action']=='purge_delete_invalid' and float(r['time'])<float(first['time']) for r in bl)
    if j['case']=='after_delete': state_ok=state_ok and bool(initial_invalid) and bool(initial_delete) and float(initial_delete['time'])<float(first['time'])
    if j['case']=='cold': state_ok=state_ok and not [r for r in bl if float(r['time'])<at]
    count_ok=row['planned']==row['accepted']==4 and len({r['seq'] for r in rx})==len(rx) and {r['seq'] for r in rx}<={'0','1','2','3'}
    check=dict(case=j['case'],seed=j['seed'],version=j['version'],qualified=bool(state_ok),four_packet_schedule_exact=scheduled,four_accepted_no_duplicate_deliveries=count_ok,actual_B_state=row['actual_B_state'],first_B_lookup_s=first['time'] if first else None,old_next_hop=first['next_hop'] if first else None,remaining_lifetime_s=first['route_lifetime'] if first else None,initial_invalidation_s=initial_invalid['time'] if initial_invalid else None,initial_invalidation_action=initial_invalid['action'] if initial_invalid else None,first_delete_s=initial_delete['time'] if initial_delete else None)
    checks.append(check)
    if j['version']=='stock' and j['case'] in ['retained','after_delete']:
        timeline.append(dict(case=j['case'],seed=j['seed'],version='stock',invalidation_s=initial_invalid['time'],invalidation_action=initial_invalid['action'],delete_s=initial_delete['time'],main_at_s=at,first_B_lookup_s=first['time'],actual_B_state=row['actual_B_state']))
    if retained and j['version']=='patch':
        zero=next(r for r in rx if r['seq']=='0');timings.append(dict(case=j['case'],seed=j['seed'],version=j['version'],seq0_arrival_s=zero['time'],first_send_s=at,seq0_wait_ms=(float(zero['time'])-at)*1000))
for case in ['retained','after_delete','cold','second']:
    for seed in [1,2,3]:
        pair={v:next(r for r in rows if r['case']==case and r['seed']==seed and r['version']==v) for v in ['stock','patch']};at=pair['stock']['mainAt']
        data={v:{ext:read(runs/f'{case}-{seed}-{v}-{ext}.csv') for ext in ['events','control-events']} for v in pair}
        prefixes.append(dict(case=case,seed=seed,pre_main_control_exact_equal=[r for r in data['stock']['control-events'] if float(r['time'])<at]==[r for r in data['patch']['control-events'] if float(r['time'])<at],pre_main_application_exact_equal=[r for r in data['stock']['events'] if float(r['time'])<at]==[r for r in data['patch']['events'] if float(r['time'])<at]))
        delivery.append(dict(case=case,seed=seed,planned_per_implementation=4,stock_received=pair['stock']['received_final'],patch_received=pair['patch']['received_final']))
write_csv(output/'F2_timeline.csv',timeline);write_csv(output/'F3_matrix.csv',delivery);write_csv(output/'diagnostic_first_packet.csv',timings);write_csv(output/'qualifications.csv',checks);write_csv(output/'paired_prefixes.csv',prefixes)
# Expected identities are small code-side metadata; original CSV bytes need not be installed.
originals=json.loads((P/'PROVENANCE.json').read_text())['original_raw_csv']
assert len(originals)==120, 'Expected exactly 120 required original trace identities'
raw_comparisons=[]
reference_comparisons=[]
for record in originals:
    name=Path(record['path']).name; actual=runs/name
    raw_comparisons.append(dict(file='runs/'+name,sha256=record['sha256'],exact=actual.is_file() and sha(actual)==record['sha256']))
    if reference_runs is not None:
        reference=reference_runs/name
        reference_comparisons.append(dict(file='runs/'+name,reference_matches_original_hash=reference.is_file() and sha(reference)==record['sha256'],exact=actual.is_file() and reference.is_file() and actual.read_bytes()==reference.read_bytes()))
summary_equal=json.loads((output/'SUMMARY.json').read_text())==json.loads((P/'expected/SUMMARY.json').read_text())
matrix_equal=(output/'matrix.csv').read_bytes()==(P/'expected/matrix.csv').read_bytes()
all_qualified=all(r['qualified'] and r['four_packet_schedule_exact'] and r['four_accepted_no_duplicate_deliveries'] for r in checks)
all_prefixes=all(r['pre_main_control_exact_equal'] and r['pre_main_application_exact_equal'] for r in prefixes)
report=dict(total_runs=len(rows),whole_run_pairs=len(prefixes),all_state_and_packet_checks_pass=all_qualified,all_paired_prefixes_exact=all_prefixes,original_summary_exact=summary_equal,original_matrix_bytes_exact=matrix_equal,original_raw_csv_compared=len(raw_comparisons),original_raw_csv_exact=sum(r['exact'] for r in raw_comparisons),diagnostic_patch_retention_wait_ms_min=min(r['seq0_wait_ms'] for r in timings),diagnostic_patch_retention_wait_ms_max=max(r['seq0_wait_ms'] for r in timings),timeline_invalidation_actions=sorted(set(r['invalidation_action'] for r in timeline)),checks=checks,raw_comparisons=raw_comparisons,limitations=['Four packets within a run are not independent replications.','Undelivered through 60 s is right-censored, not permanent failure.','Run 1 invalidates via RERR; runs 2 and 3 invalidate during purge.','The six first-packet timing records are the two retention motifs with INVALID-only, not cold-start or post-deletion runs.'])
report['raw_identity_method']='Input CSV SHA-256 compared with pinned original identities; no bundled raw traces required.'
report['reference_input_supplied']=reference_runs is not None
report['reference_raw_csv_compared']=len(reference_comparisons)
report['reference_raw_csv_bytes_exact']=sum(r['exact'] for r in reference_comparisons)
report['reference_raw_csv_original_hash_exact']=sum(r['reference_matches_original_hash'] for r in reference_comparisons)
report['reference_comparisons']=reference_comparisons
report['pass_all']=len(rows)==24 and all_qualified and all_prefixes and summary_equal and matrix_equal and all(r['exact'] for r in raw_comparisons) and all(r['exact'] and r['reference_matches_original_hash'] for r in reference_comparisons)
(output/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Validation:',json.dumps({k:v for k,v in report.items() if k not in ['checks','raw_comparisons','reference_comparisons','limitations']}))
if a.check_expected and not report['pass_all']: raise SystemExit('FAIL: expected evidence, state, schedule or prefix mismatch; see validation.json')
