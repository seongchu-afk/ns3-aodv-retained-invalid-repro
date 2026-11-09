"""Validate a NEW queue observer, not the missing original supplementary observer."""
from pathlib import Path
import argparse,csv,json
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);a=p.parse_args();W=a.work
with (W/'natural95/runs/stock-queue.csv').open() as f:rows=list(csv.DictReader(f))
rows=[x for x in rows if x['source']=='10.1.1.1' and x['destination']=='10.1.1.4']
evicted=[x for x in rows if x['reason']=='Drop the most aged packet'];exhausted=[x for x in rows if x['reason'].strip()=='DropPacketWithDst']
assert len(evicted)==31 and [int(x['sequence']) for x in evicted]==list(range(31))
assert abs(float(evicted[0]['time'])-24.9)<1e-9 and abs(float(evicted[-1]['time'])-27.9)<1e-9
assert len(exhausted)==64 and [int(x['sequence']) for x in exhausted]==list(range(31,95))
assert all(abs(float(x['time'])-28.58)<1e-9 for x in exhausted)
result={'observer':'New supplementary read-only observer, not recovered original source','fifo_evictions':31,'retry_exhaustion_drops':64,'pass':True}
(W/'NEW_QUEUE_OBSERVER_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
