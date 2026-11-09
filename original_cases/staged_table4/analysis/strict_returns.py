"""Read-only physical IP/application return detection, with auditable event pairs."""
import csv,collections,hashlib
from decimal import Decimal
IDENTITY_FIELDS=('ip_source','ip_destination','ip_protocol','ip_id','flow','seq')
REQUIRED=set(IDENTITY_FIELDS)|{'node','time','order','event','interface','ttl','kind','packet_uid'}
def detect_returns(path,evidence_path=None):
 prior=collections.defaultdict(list);identities=set();source=set();weak=set();other=set();evidence=[];data_rows=0;loopback=0
 with path.open(newline='') as f:
  reader=csv.DictReader(f);assert REQUIRED<=set(reader.fieldnames),f'Missing fields: {path}'
  previous_order=-1
  for line,row in enumerate(reader,2):
   order=int(row['order']);assert order>previous_order,f'Non-monotonic observation order: {path}:{line}';previous_order=order
   if row['kind']!='DATA':continue
   data_rows+=1
   if int(row['interface'])==0:loopback+=1;continue
   assert row['event'] in ['TX','RX']
   assert all(row[k] not in ['',None] for k in REQUIRED),f'Incomplete DATA identity: {path}:{line}'
   assert all(int(row[k])>=0 for k in ['flow','seq','ip_id','ip_protocol','ttl','interface'])
   key=(row['node'],)+tuple(row[k] for k in IDENTITY_FIELDS);time=Decimal(row['time']);ttl=int(row['ttl'])
   main=row['node']=='0' and row['flow']=='1' and row['ip_source']=='10.1.1.1'
   if row['event']=='TX':prior[key].append((time,ttl,line,row));continue
   if main and row['interface']=='1':weak.add(int(row['seq']))
   # Strictly earlier printed timestamp, not merely earlier row/order; both events non-loopback.
   match=next((x for x in reversed(prior[key]) if x[0]<time and x[1]>ttl),None)
   if match is None:continue
   identities.add(key)
   if main and row['interface']=='1':source.add(int(row['seq']))
   else:other.add(key)
   _,_,tx_line,tx=match
   ev={'node':row['node'],**{k:row[k] for k in IDENTITY_FIELDS},'tx_line':tx_line,'rx_line':line,'tx_time':tx['time'],'rx_time':row['time'],'tx_order':tx['order'],'rx_order':row['order'],'tx_interface':tx['interface'],'rx_interface':row['interface'],'tx_ttl':tx['ttl'],'rx_ttl':row['ttl'],'tx_packet_uid':tx['packet_uid'],'rx_packet_uid':row['packet_uid']}
   evidence.append(ev)
 if evidence_path is not None:
  evidence_path.parent.mkdir(parents=True,exist_ok=True)
  fields=['node',*IDENTITY_FIELDS,'tx_line','rx_line','tx_time','rx_time','tx_order','rx_order','tx_interface','rx_interface','tx_ttl','rx_ttl','tx_packet_uid','rx_packet_uid']
  with evidence_path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(evidence)
 return {'source_main_sequences':sorted(source),'legacy_weak_source_sequences':sorted(weak),'any_node_identity_count':len(identities),'other_node_or_flow_identity_count':len(other),'matched_rx_event_count':len(evidence),'data_trace_rows':data_rows,'excluded_loopback_data_rows':loopback,'control_csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'first_evidence':evidence[0] if evidence else None}
