from pathlib import Path
import csv,json,collections,math,argparse
from strict_returns import detect_returns
parser=argparse.ArgumentParser();parser.add_argument('--input-root',type=Path,required=True);parser.add_argument('--output-root',type=Path,default=Path(__file__).resolve().parent);args=parser.parse_args();P=args.input_root.resolve();O=args.output_root.resolve();O.mkdir(parents=True,exist_ok=True)
assert P!=O,'Refuse to overwrite delivered analysis'
corrections=[]
all_windows=[];summaries=[]
for suite in ['temporal','counterexample','combined']:
 for d in sorted((P/(suite+'_runs')).iterdir()):
  if not (d/'status.json').exists():continue
  st=json.loads((d/'status.json').read_text());assert st['exit_code']==0,str(d)
  c=st['config'];duration=float(c.get('trafficDuration',40));start=18.5 if suite in ['counterexample','combined'] else 9.15
  if suite in ['counterexample','combined'] and 'trafficDuration' not in c:duration=.4
  event=list(csv.DictReader(open(d/'trace-events.csv')))
  tx={int(x['seq']):float(x['time']) for x in event if x['flow']=='1' and x['event']=='tx' and x['unique_or_send_ok']=='1'}
  rx={int(x['seq']):float(x['time']) for x in event if x['flow']=='1' and x['event']=='rx' and x['unique_or_send_ok']=='1'}
  windows=[]
  for w in range(math.floor(duration+1e-9)):
   seqs=[q for q,t in tx.items() if start+w-1e-7<=t<start+w+1-1e-7]
   n=len(seqs);eventual=sum(q in rx for q in seqs);timely=sum(q in rx and rx[q]-tx[q]<=1 for q in seqs)
   row=dict(suite=suite,case=d.name,window=w,start_s=start+w,n=n,eventual_received=eventual,within1s=timely,eventual_rate=eventual/n if n else None,timely_rate=timely/n if n else None)
   windows.append(row);all_windows.append(row)
  def recovery(field):
   for i in range(len(windows)-4):
    if all(x[field] is not None and x[field]>=.8 for x in windows[i:i+5]):return windows[i]['start_s']
   return None
  rx_times=sorted(rx.values());active_end=start+duration;active_arrivals=[t for t in rx_times if start<=t<=active_end];gaps=[b-a for a,b in zip([start]+active_arrivals,active_arrivals+[active_end])]
  final_seqs=[q for q,t in tx.items() if t>=max(start,active_end-5)-1e-7]
  snapshots=collections.defaultdict(list)
  for x in csv.DictReader(open(d/'trace-route-snapshots.csv')):snapshots[int(x['snapshot'])].append(x)
  pending={};lineage=[];overlap=[];cycle_times=[]
  for sid,ss in snapshots.items():
   now=float(ss[0]['time']);search=[int(x['node']) for x in ss if x['present']=='1' and x['flag']=='2']
   if len(search)>=2:overlap.append({'time':now,'nodes':search})
   active={int(x['node']):int(x['next_hop'].split('.')[-1])-1 for x in ss if x['present']=='1' and x['flag']=='0' and float(x['expiry'])>now}
   cyc=False
   for a in active:
    path=[];cur=a
    while cur in active and cur!=3:
     if cur in path:
      if len(path[path.index(cur):])>=2:cyc=True
      break
     path.append(cur);cur=active[cur]
   cycle_times.append((now,cyc))
   for x in ss:
    node=x['node'];flag=x['flag']
    if flag=='1' and node not in pending:pending[node]={'start':now,'via_search':False}
    elif flag=='2' and node in pending:pending[node]['via_search']=True
    elif flag=='0' and node in pending:lineage.append(dict(node=node,invalid_at=pending[node]['start'],valid_at=now,via_search=pending[node]['via_search']));del pending[node]
    elif x['present']=='0':pending.pop(node,None)
  # End-of-timestamp states distinguish synchronous transient cycles from persisting states.
  final_at_time={t:c for t,c in cycle_times};ordered=sorted(final_at_time.items());cycle_duration=sum(ordered[i+1][0]-t for i,(t,c) in enumerate(ordered[:-1]) if c)
  strict=detect_returns(d/'trace-control-events.csv',O/'return_evidence'/suite/(d.name+'.csv'));returned=set(strict['source_main_sequences'])
  corrections.append(dict(suite=suite,case=d.name,**strict))
  reasons=list(csv.DictReader(open(d/'trace-reason.csv')))
  relevant=[x for x in reasons if x['node']=='1' and x['origin']=='10.1.1.1' and x['destination']=='10.1.1.4' and float(x['time'])>=start and x['reason']=='destination_route_present']
  first=relevant[0] if relevant else None
  retained=bool(first and first['route_flag']=='1' and first['next_hop']=='10.1.1.1' and float(first['route_lifetime'])>0)
  graph=list(csv.DictReader(open(d/'trace-graph.csv')));near=[x for x in graph if x['flow']=='1' and float(x['time'])<=start+1e-8];main_tx=[x for x in event if x['flow']=='1' and x['event']=='tx'];hops=int(main_tx[0]['at_send_geometry_hops']) if main_tx else -1
  bypass=[x for x in reasons if x['reason']=='invalid_route_guard_bypassed']
  # Exact reason labels retained below, allowing independent auditing rather than assumed terminology.
  result=dict(suite=suite,case=d.name,config=c['name'],version=st['version'],run=st['run'],sent=len(tx),received=len(rx),first_rx=min(rx_times) if rx_times else None,last_rx=max(rx_times) if rx_times else None,observation_stop=100 if suite in ['counterexample','combined'] else 90,delivery_censored=not bool(rx),duration_s=duration,recovery_assessable=duration>=5,first_eventual_qualifying_generation_cohort_start_s=recovery('eventual_rate'),first_timely_qualifying_generation_cohort_start_s=recovery('timely_rate'),longest_active_rx_gap_s=max(gaps) if gaps else duration,final5s_generated=len(final_seqs),final5s_eventual_received=sum(q in rx for q in final_seqs),final5s_timely_received=sum(q in rx and rx[q]-tx[q]<=1 for q in final_seqs),initial_geometry_hops=hops,retained_invalid_qualified=retained,positive_perturbation_qualified=st.get('qualification_pass') if suite=='temporal' else None,artificial_perturbation_qualified=st.get('qualification_pass') if suite=='temporal' else None,first_relevant_route=first,reactivation_lineage=lineage,concurrent_search_observed=bool(overlap),first_overlap=overlap[0] if overlap else None,cycle_any_snapshot=any(c for t,c in cycle_times),observed_end_of_timestamp_cycle_duration_s=cycle_duration,cycle_end_of_timestamp_count=sum(final_at_time.values()),returned_main_packet_sequences=sorted(returned),strict_source0_main_return_count=len(returned),strict_any_observed_node_identity_count=strict['any_node_identity_count'],strict_other_node_or_flow_identity_count=strict['other_node_or_flow_identity_count'],strict_matched_rx_event_count=strict['matched_rx_event_count'],reason_labels=dict(collections.Counter(x['reason'] for x in reasons)))
  output_case=O/(suite+'_runs')/d.name;output_case.mkdir(parents=True,exist_ok=True)
  (output_case/'extended_analysis.json').write_text(json.dumps(result,indent=2));summaries.append(result)
(O/'TEMPORAL_EXTENDED.json').write_text(json.dumps(summaries,indent=2))
for name,rows in [('recovery_windows',all_windows),('temporal_extended_summary',[{k:v for k,v in r.items() if k not in ['first_relevant_route','reactivation_lineage','first_overlap','reason_labels','returned_main_packet_sequences']} for r in summaries])]:
 with (O/(name+'.csv.tmp')).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (O/(name+'.csv.tmp')).replace(O/(name+'.csv'))
print(json.dumps([r for r in summaries if r['config'] in ['baseline','concurrent1']],indent=2))

# Export natural qualifications by their actual gate, not the inapplicable artificial perturbation gate.
for suite in ['counterexample','combined']:
 rows=[{k:x[k] for k in ['case','config','version','run','sent','received','first_rx','last_rx','retained_invalid_qualified','concurrent_search_observed']}|{'artificial_perturbation_qualified':None} for x in summaries if x['suite']==suite]
 with (O/(suite+'_summary.csv.tmp')).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (O/(suite+'_summary.csv.tmp')).replace(O/(suite+'_summary.csv'))

(O/"STRICT_RETURN_RESULTS.json").write_text(json.dumps(corrections,indent=2))
