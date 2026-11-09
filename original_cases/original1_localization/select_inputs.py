# SPDX-License-Identifier: GPL-2.0-only
"""Select source evidence for the original-environment-1 localization example."""
from pathlib import Path
import argparse,csv,json,hashlib,shutil

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def select(work,out):
    source=work/'six/runs';assert source.is_dir();out.mkdir(parents=True,exist_ok=False);rec=[]
    for v in ['stock','patch']:
        for suffix in ['events','reasons','control-events']:
            n=f'original1-{v}-{suffix}.csv';p=source/n;q=out/n
            with p.open(newline='') as f:r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
            if suffix=='events':shutil.copyfile(p,q);kept=rows;rule='None. Full original application-event CSV preserved byte-for-byte to retain all-flow comparisons.'
            else:
                kept=[r for r in rows if r['origin']=='10.1.1.5' and r['destination']=='10.1.1.25' and (suffix!='control-events' or r['kind']=='RREQ')]
                with q.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(kept)
                rule='Keep all target origin 10.1.1.5 and destination 10.1.1.25 records'+(' with kind RREQ.' if suffix=='control-events' else '.')+' Field values and order preserved; serialize with Python csv default CRLF.'
            rec.append({'path':n,'source':'six/runs/'+n,'source_sha256':sha(p),'sha256':sha(q),'source_rows':len(rows),'selected_rows':len(kept),'transformation':rule})
    (out/'PROVENANCE.json').write_text(json.dumps({'scope':'Original-environment-1 final-delivery and request-localization example, selected from the fresh original six-environment rerun. Recreate full traces through original_tables build/run --suite six.','files':rec},indent=2)+'\n')
    fs=[{'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.iterdir()) if p.is_file()];(out/'MANIFEST.json').write_text(json.dumps({'version':'2.0.1-candidate','files':fs},indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();select(a.work,a.output)
