"""Post hoc spatial thinning of the 500 m map-pair comparison.

Select exactly one accepted 500 m cell per occupied anchored block, separately
within each event, without replacement inside each block. Paired sensor counts
and location remain unchanged. This is a population-changing sensitivity, not a
bootstrap CI and does not guarantee spatial independence across adjacent blocks.
"""
from pathlib import Path
import json
import numpy as np,pandas as pd
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parents[2]
f=ROOT/'inputs/primary_500m_cells.parquet'
old=pd.read_csv(ROOT/'inputs/historical_hls_sar_per_event_metrics.csv')
out=Path(__file__).resolve().parent
ids=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
fields=['strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count']
d=pd.read_parquet(f,columns=['event_id','x_index','y_index','strict_common_valid_coverage']+fields)
d=d[d.event_id.isin(ids)&d.strict_common_valid_coverage.ge(.95)&d.strict_common_valid_pixel_count.gt(0)]
SEED=20261116;REPS=300;rng=np.random.default_rng(SEED)
def metrics(frame):
 n=len(frame);k=int(np.ceil(.2*n));x=frame.x_index.to_numpy();y=frame.y_index.to_numpy()
 den=frame[fields[0]].to_numpy()
 a=frame[fields[1]].to_numpy()/den;b=frame[fields[2]].to_numpy()/den
 ia=np.lexsort((y,x,-a));ib=np.lexsort((y,x,-b))
 overlap=np.intersect1d(ia[:k],ib[:k]).size/k
 rho=float(spearmanr(a,b).statistic) if len(np.unique(a))>1 and len(np.unique(b))>1 else np.nan
 def prob(s):
  t=np.sort(s)[-k];gt=s>t;eq=s==t
  return gt.astype(float)+eq.astype(float)*(k-gt.sum())/eq.sum()
 tie_expected=float(np.dot(prob(a),prob(b))/k)
 return rho,overlap,tie_expected,n,k
results=[];summary=[]
for event,g in d.groupby('event_id',sort=True):
 base=metrics(g);r=old[(old.event_id==event)&np.isclose(old.scale_km,.5)&np.isclose(old.budget,.2)].iloc[0]
 assert base[3]==int(r.n_cells) and base[4]==int(r.k) and np.isclose(base[1],r.topk_overlap,atol=1e-12)
 for size in [2.5,5.0]:
  fct=int(size*2);key=np.stack([g.x_index.to_numpy()//fct,g.y_index.to_numpy()//fct],axis=1)
  _,inv=np.unique(key,axis=0,return_inverse=True)
  ordered=np.argsort(inv,kind='stable');counts=np.bincount(inv);starts=np.cumsum(np.r_[0,counts[:-1]])
  vals=[]
  for draw in range(REPS):
   selected=ordered[starts+(rng.random(len(counts))*counts).astype(int)]
   z=metrics(g.iloc[selected]);vals.append(z[:3])
   results.append(dict(event_id=event,block_km=size,draw=draw+1,n_units=z[3],k=z[4],spearman=z[0],coordinate_overlap=z[1],random_cutoff_overlap=z[2]))
  a=np.asarray(vals)
  row=dict(event_id=event,block_km=size,accepted_cells=base[3],thinned_cells=len(counts),baseline_rho=base[0],baseline_coordinate_overlap=base[1],baseline_random_cutoff_overlap=base[2])
  for j,name in enumerate(['spearman','coordinate_overlap','random_cutoff_overlap']):
   valid=a[np.isfinite(a[:,j]),j]; row[name+'_defined_draws']=len(valid)
   for q,v in zip(('q025','median','q975'),np.quantile(valid,[.025,.5,.975]) if len(valid) else [np.nan]*3):row[name+'_'+q]=v
  summary.append(row)
pd.DataFrame(results).to_csv(out/'thinned_map_metrics_draws.csv',index=False)
pd.DataFrame(summary).to_csv(out/'thinned_map_metrics_summary.csv',index=False)
(out/'thinning_manifest.json').write_text(json.dumps({'seed':SEED,'draws_per_event_and_block':REPS,'methods':'one uniformly sampled accepted cell per occupied block, paired scores preserved','limitations':['selection population changes','neighbor blocks can remain spatially dependent','quantiles are thinning sensitivity ranges, not confidence intervals','all choices were post hoc']},indent=2),encoding='utf8')
print(pd.DataFrame(summary).to_string(index=False))

