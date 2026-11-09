# SPDX-License-Identifier: GPL-2.0-only
"""Deterministically select Figure 5 inputs from the original six-environment run."""
from pathlib import Path
import argparse,csv,json,hashlib

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def select(work,out):
    source=work/'six/runs';assert source.is_dir();out.mkdir(parents=True,exist_ok=False);records=[]
    for v in ['stock','patch']:
        for suffix in ['events','arp-l3-drop','arp-state','control-events','airtime']:
            name=f'rwp3-{v}-{suffix}.csv';p=source/name
            with p.open(newline='') as f:
                reader=csv.DictReader(f);fields=reader.fieldnames;allrows=list(reader)
            if suffix=='arp-state':rows=[r for r in allrows if r['node']=='7' and r['peer']=='19'];rule='Keep all recorded rows with node == 7 and peer == 19.'
            else:
                rows=[r for r in allrows if r['flow']=='2' and (suffix not in ['control-events','airtime'] or r['kind']=='DATA')]
                rule='Keep all flow == 2 rows'+(' with kind == DATA.' if suffix in ['control-events','airtime'] else '.')
            q=out/name
            with q.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
            records.append({'path':name,'source':'six/runs/'+name,'source_sha256':sha(p),'sha256':sha(q),'source_rows':len(allrows),'selected_rows':len(rows),'transformation':rule+' Preserve field order and values; serialize CSV with Python csv default CRLF line endings.'})
    (out/'PROVENANCE.json').write_text(json.dumps({'scope':'Deterministic Figure 5 selections from the original six-environment observer outputs. No lost sequence is selected by the extraction rule; all flow-2 application and DATA events are retained. Recreate the full inputs using original_tables build.py/run.py for the six suite, then run select_inputs.py.','input_generation':'Reference inputs were selected from a fresh scientific-harness rerun against the official clean ns-3.47 base.','files':records},indent=2)+'\n')
    files=[{'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.iterdir()) if p.is_file()]
    (out/'MANIFEST.json').write_text(json.dumps({'version':'2.0.1-candidate','files':files},indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();select(a.work,a.output)
