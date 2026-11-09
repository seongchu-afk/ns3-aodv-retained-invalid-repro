from pathlib import Path
import json,csv,numpy as np
from scipy.stats import t
P=Path(__file__).resolve().parent
res=json.loads((P/'ENSEMBLE_COMPLETE.json').read_text())['results'];expected={(e,r,v) for e in ['original1','original2','original3','rwp1','rwp2','rwp3'] for r in range(101,121) for v in ['stock','patch']}
keys=[(x['environment'],x['run'],x['version']) for x in res]
assert len(keys)==len(set(keys))==240 and set(keys)==expected,'Missing, duplicate or unexpected run key'
assert all(x['exit_code']==0 for x in res),'Failed ensemble run'
ok=res;rows=[];summary=[];rng=np.random.default_rng(20261109)
for env in sorted(set(x['environment'] for x in res)):
 pairs=[]
 for run in range(101,121):
  d={x['version']:x for x in ok if x['environment']==env and x['run']==run}
  assert set(d)=={'stock','patch'},f'Incomplete pair: {env} {run}'
  row={'environment':env,'run':run}
  for m in ['received','pdr','control_bytes','control_frames','control_airtime_ns','retry_frames','app_window_control_bytes','app_window_control_frames','app_window_control_airtime_ns']:
   for v in ['stock','patch']:row[v+'_'+m]=d[v][m]
   row['delta_'+m]=d['patch'][m]-d['stock'][m]
  rows.append(row);pairs.append(row)
 assert len(pairs)==20,f'Expected20 pairs in {env}'
 for m in ['received','pdr','control_bytes','control_frames','control_airtime_ns','retry_frames','app_window_control_bytes','app_window_control_frames','app_window_control_airtime_ns']:
  a=np.array([x['delta_'+m] for x in pairs],float);n=len(a);mean=float(a.mean());se=float(a.std(ddof=1)/np.sqrt(n));ci=t.ppf(.975,n-1)*se;boot=rng.choice(a,(10000,n),replace=True).mean(1)
  summary.append(dict(environment=env,metric=m,n_pairs=n,stock_mean=float(np.mean([x['stock_'+m] for x in pairs])),patch_mean=float(np.mean([x['patch_'+m] for x in pairs])),stock_sd=float(np.std([x['stock_'+m] for x in pairs],ddof=1)),patch_sd=float(np.std([x['patch_'+m] for x in pairs],ddof=1)),delta_sd=float(a.std(ddof=1)),delta_mean=mean,delta_median=float(np.median(a)),delta_min=float(a.min()),delta_max=float(a.max()),positive=int(sum(a>0)),zero=int(sum(a==0)),negative=int(sum(a<0)),ci95_t_low=mean-ci,ci95_t_high=mean+ci,ci95_boot_low=float(np.quantile(boot,.025)),ci95_boot_high=float(np.quantile(boot,.975))))
for name,data in [('paired_runs',rows),('ensemble_summary',summary)]:
 (P/(name+'.json')).write_text(json.dumps(data,indent=2))
 with (P/(name+'.csv')).open('w') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
print(json.dumps([x for x in summary if x['metric'] in ['received','pdr','control_bytes']],indent=2))
