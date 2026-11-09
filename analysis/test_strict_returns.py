"""Synthetic analysis-unit tests only; these do not run any network simulation."""
from pathlib import Path
import csv,json,tempfile
from strict_returns import detect_returns
P=Path(__file__).resolve().parent
base=dict(node='0',ip_source='10.1.1.1',ip_destination='10.1.1.4',ip_protocol='17',ip_id='3',flow='1',seq='7',time='1',event='TX',interface='1',ttl='64',kind='DATA',packet_uid='42')
def tx(**kw):return dict(base,**kw)
def rx(**kw):return dict(base,**{'event':'RX','time':'2','ttl':'63',**kw})
tests=[('strict_return',[tx(),rx()],1,1),('no_prior_tx',[rx()],0,0),('same_timestamp_not_earlier',[tx(),rx(time='1')],0,0),('ttl_equal',[tx(),rx(ttl='64')],0,0),('ttl_increased',[tx(),rx(ttl='65')],0,0),('tx_loopback',[tx(interface='0'),rx()],0,0),('rx_loopback',[tx(),rx(interface='0')],0,0),('different_node',[tx(),rx(node='1')],0,0),('different_ipv4_id',[tx(),rx(ip_id='4')],0,0),('different_app_seq',[tx(),rx(seq='8')],0,0),('different_flow',[tx(),rx(flow='2')],0,0),('different_destination',[tx(),rx(ip_destination='10.1.1.3')],0,0),('uid_auxiliary_only',[tx(),rx(packet_uid='99')],1,1),('two_returns_one_identity',[tx(),rx(),rx(time='3',ttl='62')],1,2),('general_forwarding_node',[tx(node='2',ip_source='10.1.1.5',flow='2'),rx(node='2',ip_source='10.1.1.5',flow='2')],1,1)]
results=[]
with tempfile.TemporaryDirectory(dir=P) as tmp:
 for name,rows,count,events in tests:
  rows=[dict(r,order=str(i)) for i,r in enumerate(rows)];f=Path(tmp)/(name+'.csv')
  with f.open('w') as out:w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
  r=detect_returns(f);assert r['any_node_identity_count']==count and r['matched_rx_event_count']==events,name
  if name=='general_forwarding_node':assert r['source_main_sequences']==[] and r['other_node_or_flow_identity_count']==1
  results.append({'test':name,'passed':True})
(P/'ANALYSIS_UNIT_TESTS.json').write_text(json.dumps(results,indent=2));print('Passed',len(results),'synthetic analysis tests;0simulations.')
