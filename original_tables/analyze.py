"""Compare regenerated original evidence with manuscript supplementary tables."""
from pathlib import Path
import argparse,csv,json,math
P=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--smoke',action='store_true',help='Validate handler and natural95 only; omit six environments');p.add_argument('--work',type=Path,required=True);a=p.parse_args();W=a.work.resolve()
def read(p):
 with Path(p).open(newline='') as f:return list(csv.DictReader(f))
def write(name,rows):
 with (W/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
ref=read(P/'reference/Table_S1_handler_99_cases.csv');handler=[]
for v in ['stock','patch']:
 pre=W/'handler/runs'/v;cases=read(str(pre)+'-cases.csv');reasons=read(str(pre)+'-reasons.csv');packets=read(str(pre)+'-packets.csv');assert len(cases)==99
 for c,r in zip(cases,ref):
  n=int(c['request_id']);assert n==int(r['case_id'])
  flag=int(c['flag']);same=int(c['next_same']);cv=int(c['cache_valid']);sc=int(c['seq_case']);req=int(c['request_seq']);D=int(c['D']);ttl=int(c['TTL']);known=cv and (sc==0 or 10>=req)
  expected='loop_guard_next_hop_equals_sender' if same and (v=='stock' or flag!=1) else 'intermediate_reply' if known and flag==0 and not D else 'ttl_exhausted' if ttl<2 else 'forward_scheduled'
  actual=[x['reason'] for x in reasons if int(x['request_id'])==n];sent=[x for x in packets if int(x['request_id'])==n]
  assert actual==[expected]==[r[v+'_observed_branch']]
  assert (int(c['post_flag']),int(c['post_seq']),int(c['post_valid']),c['post_next'])==(flag,10,cv,'10.1.1.1' if same else '10.1.1.3')
  assert float(c['post_lifetime'])==100 and int(c['simulation_time_ns'])==1
  if expected=='forward_scheduled':
   assert len(sent)==1
   assert (int(sent[0]['destination_seq']),int(sent[0]['unknown']),int(sent[0]['hop']),int(sent[0]['ttl']))==(10 if known else req,0 if known else int(sc==0),1,ttl-1)
  else:assert not sent
  handler.append({'version':v,'case_id':n,'observed_branch':actual[0],'pass':True})
write('handler_verification.csv',handler)
if not a.smoke:
 rows=[]
 for family in ['original','rwp']:
  for seed in [1,2,3]:
   rx={};planned={};air={}
   for v in ['stock','patch']:
    pre=W/'six/runs'/f'{family}{seed}-{v}';e=read(str(pre)+'-events.csv');airtime=read(str(pre)+'-airtime.csv')
    rx[v]={(int(x['flow']),int(x['seq'])) for x in e if x['event']=='rx' and x['unique_or_send_ok']=='1'}
    planned[v]=[(x['time'],x['flow'],x['seq'],x['bytes_or_send_result']) for x in e if x['event']=='tx']
    air[v]=sum(int(x['duration_ns']) for x in airtime if 60<=float(x['time'])<180 and x['kind'] in {'RREQ','RREP','HELLO','RERR','RREP_ACK'})/1e9
   assert planned['stock']==planned['patch']
   rows.append(dict(environment=('Original' if family=='original' else 'RWP')+' '+str(seed),planned=len(planned['stock']),gained=len(rx['patch']-rx['stock']),lost=len(rx['stock']-rx['patch']),net=len(rx['patch'])-len(rx['stock']),stock_received=len(rx['stock']),patch_received=len(rx['patch']),stock_AODV_tx_s=air['stock'],patch_AODV_tx_s=air['patch']))
 reference=read(P/'reference/Table_S4_six_environment_metrics.csv')
 for row,r in zip(rows,reference):
  for key,value in row.items():
   if key=='environment':assert value==r[key]
   elif key.endswith('_tx_s'):assert abs(value-float(r[key]))<=5.01e-7,(key,value,r[key])
   else:assert value==int(r[key]),(row,key,r[key])
 write('Table_S4_regenerated.csv',rows)
nat={}
for v in ['stock','patch']:
 pre=W/'natural95/runs'/v;e=read(str(pre)+'-events.csv');rx=[x for x in e if x['event']=='rx' and x['unique_or_send_ok']=='1'];main=[x for x in rx if x['flow']=='1'];tx=[x for x in e if x['event']=='tx' and x['flow']=='1']
 assert len(tx)==95 and len(main)==(0 if v=='stock' else 95)
 assert len([x for x in rx if x['flow']=='0'])==40
 nat[v]={'warmup_delivered':40,'main_sent':len(tx),'main_delivered':len(main),'first_main_rx':float(main[0]['time']) if main else None,'last_main_rx':float(main[-1]['time']) if main else None}
pre=W/'natural95/runs/stock';lc=read(str(pre)+'-lifecycle.csv');b=[x for x in lc if x['owner_ip']=='10.1.1.2' and x['destination']=='10.1.1.4'];invalid=next(x for x in b if x['action']=='rerr_after_invalidate');deleted=next(x for x in b if x['action']=='purge_delete_invalid')
assert abs(float(invalid['time'])-12.056376466)<1e-9 and abs(float(deleted['time'])-27.073192233)<1e-9
control=read(str(pre)+'-control-events.csv');req=[x for x in control if x['event']=='TX' and x['kind']=='RREQ' and x['node']=='0' and float(x['time'])>=18.5];assert [int(x['ttl']) for x in req]==[3,5,7,35,35]
shots=read(str(pre)+'-route-snapshots.csv');absent=[x for x in shots if x['node']=='0' and x['present']=='0' and float(x['time'])>=18.5];assert abs(float(absent[0]['time'])-28.58)<1e-9
nat.update(invalidation_s=float(invalid['time']),retention_deadline_s=float(invalid['time'])+float(invalid['lifetime']),deletion_s=float(deleted['time']),source_absence_s=float(absent[0]['time']),rreq_ttls=[int(x['ttl']) for x in req],queue_evidence='Queue eviction counts are retained in S3 reference but not directly regenerated by these historical sources. See README.')
(W/'natural95_verification.json').write_text(json.dumps(nat,indent=2)+'\n')
(W/'VALIDATION.json').write_text(json.dumps({'S1_cases_checked':198,'S2':'Exact settings reference retained; not a generated outcome table.','S3':'Application, RREQ, lifecycle and source-absence times verified. Historical additional direct queue source and trace remain unrecovered; the optional new queue observer is validated separately.','S4_six_environments_match':True if not a.smoke else 'not run in smoke mode'},indent=2)+'\n')
print('S1 198 cases and S3 timeline pass; S4 '+('not checked (smoke)' if a.smoke else 'six rows match')+'. Direct queue evidence requires the optional new observer.')
