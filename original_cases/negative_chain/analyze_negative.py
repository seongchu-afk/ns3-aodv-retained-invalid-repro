# SPDX-License-Identifier: GPL-2.0-only
"""Reproduce Figure 5 from original six-environment observer outputs.

IP TX is an IPv4-layer event that can occur before ARP succeeds. A DATA PPDU
record, rather than an IP TX alone, establishes the observed onward airtime.
"""
from pathlib import Path
import argparse,csv,json,collections,hashlib
P=Path(__file__).resolve().parent

def read(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))
def write(path,rows,fields):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def analyze(root,out):
    root=root.resolve();out=out.resolve();assert root!=out and root not in out.parents
    if (root/'MANIFEST.json').exists():
        for e in json.loads((root/'MANIFEST.json').read_text())['files']:
            assert hashlib.sha256((root/e['path']).read_bytes()).hexdigest()==e['sha256'],e['path']
    out.mkdir(parents=True,exist_ok=True)
    data={}
    for v in ['stock','patch']:
        data[v]={s:read(root/f'rwp3-{v}-{s}.csv') for s in ['events','arp-l3-drop','arp-state','control-events','airtime']}
    rx={v:{int(r['seq']) for r in d['events'] if r['flow']=='2' and r['event']=='rx' and r['unique_or_send_ok']=='1'} for v,d in data.items()}
    tx={v:[(r['time'],r['flow'],r['seq'],r['bytes_or_send_result']) for r in d['events'] if r['flow']=='2' and r['event']=='tx'] for v,d in data.items()}
    assert tx['stock']==tx['patch'] and len(tx['stock'])==1197
    assert len(rx['stock'])==1152 and len(rx['patch'])==1073
    lost=sorted(rx['stock']-rx['patch']);assert lost==list(range(206,283))+[533,534]
    arp=collections.defaultdict(list)
    for r in data['patch']['arp-l3-drop']:
        if r['flow']=='2' and int(r['seq']) in lost and r['node']=='7':arp[int(r['seq'])].append(r)
    assert sorted(arp)==list(range(208,283)) and sum(map(len,arp.values()))==75
    counts={ev:collections.Counter(int(r['seq']) for r in data['patch']['control-events'] if r['kind']=='DATA' and r['flow']=='2' and r['node']=='7' and r['event']==ev and r['interface']!='0') for ev in ['RX','TX']}
    ppdu=collections.Counter(int(r['seq']) for r in data['patch']['airtime'] if r['kind']=='DATA' and r['flow']=='2' and r['node']=='7')
    ledger=[]
    for s in lost:
        if s in arp:assert counts['RX'][s]==1 and counts['TX'][s]==1 and ppdu[s]==0
        ledger.append({'flow':2,'sequence':s,'stock_received':True,'patch_received':False,'patch_arp_drop_at_node7':s in arp,'patch_arp_drop_times_s':';'.join(r['time'] for r in arp.get(s,[])),'patch_nonloopback_ip_rx_node7':counts['RX'][s],'patch_nonloopback_ip_tx_node7':counts['TX'][s],'patch_data_ppdu_node7':ppdu[s]})
    assert sorted(set(lost)-set(arp))==[206,207,533,534]
    assert sum(r['patch_arp_drop_at_node7'] for r in ledger)==75
    write(out/'lost_packet_ledger.csv',ledger,list(ledger[0]))
    paths={};air_nodes={};iprows=[];airrows=[];states=[]
    for v,d in data.items():
        rows=[r for r in d['control-events'] if r['kind']=='DATA' and r['flow']=='2' and r['seq']=='208']
        physical=[r for r in rows if r['interface']!='0'];assert len({r['packet_uid'] for r in physical})==1
        assert all(r['ip_source']=='10.1.1.6' and r['ip_destination']=='10.1.1.20' for r in physical)
        initial=next(r for r in physical if r['event']=='TX');assert initial['node']=='5'
        paths[v]=[5]+[int(r['node']) for r in physical if r['event']=='RX']
        assert paths[v]==([5,16,10,7,19] if v=='stock' else [5,16,10,7])
        for r in rows:iprows.append({'variant':v,**r,'nonloopback':r['interface']!='0'})
        ar=[r for r in d['airtime'] if r['kind']=='DATA' and r['flow']=='2' and r['seq']=='208'];air_nodes[v]=list(dict.fromkeys(int(r['node']) for r in ar))
        assert air_nodes[v]==([5,16,10,7] if v=='stock' else [5,16,10])
        for r in ar:airrows.append({'variant':v,**r})
        sr=[r for r in d['arp-state'] if r['node']=='7' and r['peer']=='19']
        expected=[('81','ALIVE')] if v=='stock' else [('82','WAIT_REPLY'),('86','DEAD'),('89','ALIVE')]
        assert [(r['time'],r['state']) for r in sr]==expected
        for r in sr:states.append({'variant':v,**r})
    write(out/'sequence208_ip_events.csv',iprows,list(iprows[0]));write(out/'sequence208_airtime.csv',airrows,list(airrows[0]));write(out/'neighbor_state_samples.csv',states,list(states[0]))
    summary={'figure':'F5','environment':'RWP 3','flow':2,'source_node':5,'destination_node':19,'planned':1197,'stock_received':len(rx['stock']),'patch_received':len(rx['patch']),'stock_only_lost':len(lost),'lost_sequences':lost,'arp_attributed_at_node7':75,'arp_attributed_sequences':sorted(arp),'unattributed_sequences':sorted(set(lost)-set(arp)),'sequence208_observed_ip_path':paths,'sequence208_data_ppdu_transmitters':air_nodes,'state_samples':'These are recorded samples, not a continuous or interpolated neighbor-state history.','interpretation':'The ledger localizes 75 losses to observed ARP drops at node 7. It does not establish the cause of the preceding neighbor-state change. IP TX at a nonloopback interface is not by itself evidence of a DATA PPDU transmission.'}
    (out/'negative_summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check-reference',action='store_true');a=p.parse_args();result=analyze(a.input,a.output)
    if a.check_reference:
        for ref in sorted((P/'reference').iterdir()):
            if ref.suffix in ['.csv','.json']:assert (a.output/ref.name).read_bytes()==ref.read_bytes(),ref.name
    print(json.dumps({'stock_only_lost':result['stock_only_lost'],'arp_attributed_at_node7':result['arp_attributed_at_node7'],'unattributed_sequences':result['unattributed_sequences'],'all_checks_passed':True},indent=2))
