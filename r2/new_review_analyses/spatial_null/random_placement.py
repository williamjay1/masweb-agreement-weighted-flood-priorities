"""Post hoc spatial random-placement baseline for published within-product diagnostics.

The original paired cell vectors (support, S30 and L30 counts) are shuffled jointly
among fixed observed accepted cell locations, independently within each event. The
same grid occupancy and cell-level paired values are retained; spatial dependence
and association of support with location are deliberately broken. This is a
random-placement null, not a spatially structured null or validation.
"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'inputs/primary_500m_cells.parquet'
OLD=ROOT/'inputs/new_review_archives/spatial_mechanisms_per_event.csv'
OUT=Path(__file__).resolve().parent
EVENTS=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
SCALES=[1.,2.,5.,10.,20.,30.]
REPS=300
SEED=20261115
cols=['event_id','x_index','y_index','strict_common_valid_coverage','strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count']
data=pd.read_parquet(BASE,columns=cols)
data=data[data.event_id.isin(EVENTS)&data.strict_common_valid_coverage.ge(.95)&data.strict_common_valid_pixel_count.gt(0)]
old=pd.read_csv(OLD)
rng=np.random.default_rng(SEED)
rows=[];references=[]
def corr(a,b):
 a=np.asarray(a,float);b=np.asarray(b,float)
 a=a-a.mean();b=b-b.mean();den=np.sqrt(np.dot(a,a)*np.dot(b,b))
 return float(np.dot(a,b)/den) if den else np.nan
for event in EVENTS:
 g=data[data.event_id.eq(event)].copy()
 n=len(g);den=g.strict_common_valid_pixel_count.to_numpy(float)
 counts=np.stack([g.strict_s30_water_pixel_count.to_numpy(float),g.strict_l30_water_pixel_count.to_numpy(float)])
 raw=counts/den
 rawrank=np.stack([rankdata(v) for v in raw])
 print(event,n,flush=True)
 for scale in SCALES:
  f=int(scale*2)
  xy=np.stack([g.x_index.to_numpy()//f,g.y_index.to_numpy()//f],axis=1)
  _,code=np.unique(xy,axis=0,return_inverse=True);ng=int(code.max()+1)
  def stats(perm):
   w=den[perm]
   totals=np.bincount(code,weights=w,minlength=ng)
   vals=[]
   for product in range(2):
    agg=np.bincount(code,weights=counts[product,perm],minlength=ng)/totals
    persistence=corr(rawrank[product,perm],rankdata(agg[code]))
    ratio=np.std(agg,ddof=1)/np.std(raw[product],ddof=1)
    vals.append((persistence,ratio))
   return np.array(vals)
  obs=stats(np.arange(n))
  prev=old[(old.event_id==event)&np.isclose(old.scale_km,scale)]
  assert len(prev)==1
  for j,p in enumerate(('s30','l30')):
   for k,metric in enumerate(('rank_persistence','sd_ratio')):
    expected=float(prev.iloc[0][p+'_'+metric])
    assert np.isclose(obs[j,k],expected,rtol=1e-5,atol=1e-6),(event,scale,p,metric,obs[j,k],expected)
  sim=np.empty((REPS,2,2))
  for b in range(REPS):sim[b]=stats(rng.permutation(n))
  for j,p in enumerate(('s30','l30')):
   for k,metric in enumerate(('rank_persistence','sd_ratio')):
    x=sim[:,j,k];q=np.quantile(x,[.025,.5,.975])
    rows.append(dict(event_id=event,scale_km=scale,product=p,metric=metric,accepted_cells=n,aggregate_blocks=ng,observed=obs[j,k],random_q025=q[0],random_median=q[1],random_q975=q[2],draws=REPS))
out=pd.DataFrame(rows)
out.to_csv(OUT/'random_placement_event.csv',index=False)
summary=out.groupby(['scale_km','product','metric'],as_index=False).agg(events=('event_id','size'),observed_mean=('observed','mean'),random_median_mean=('random_median','mean'),random_q025_mean=('random_q025','mean'),random_q975_mean=('random_q975','mean'))
summary.to_csv(OUT/'random_placement_summary.csv',index=False)
manifest=dict(seed=SEED,draws_per_event_scale=REPS,input_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),reference_sha256=hashlib.sha256(OLD.read_bytes()).hexdigest(),reference_check='all event, product and scale observed values match within relative tolerance 1e-5 and absolute 1e-6; minor floating point differences can alter tied ranks',null='paired cell vectors shuffled together over fixed accepted positions within each event; block occupancy preserved; local spatial structure broken',limitations=['not a confidence interval or independent reference','not a spatially autocorrelated null','mean event-specific quantiles are not a joint null interval'])
(OUT/'random_placement_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print(summary.to_string(index=False))

