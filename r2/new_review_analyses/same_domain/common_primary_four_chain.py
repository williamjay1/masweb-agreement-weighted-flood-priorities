from pathlib import Path
import numpy as np,pandas as pd, hashlib, math, json
from scipy.stats import spearmanr,kendalltau
BASE=Path(__file__).resolve().parent
P=BASE/'inputs/hls_index_500m_cells.parquet'
OUT=BASE/'results';OUT.mkdir(exist_ok=True)
E=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
PRODUCTS=['dswx','mndwi','awei'];SCALES=[500,1000,2000,5000,10000,20000,30000]
d=pd.read_parquet(P);d=d[d.event_id.isin(E)].copy()
# The archived four-chain input first selects the original primary 500 m strict
# cells. Each count below refers to the same pixel intersection of S30 and L30
# DSWx and valid S30 and L30 HLS index pixels (see archived build script).
assert not d.duplicated(['event_id','x_index','y_index']).any()
assert (d.four_chain_common_pixel_count<=d.dswx_strict_common_pixel_count).all()
for p in PRODUCTS:
 for s in ['s30','l30']:
  assert (d[f'{p}_{s}_water_pixel_count']<=d.four_chain_common_pixel_count).all()
base=d[d.four_chain_strict_qualified & (d.four_chain_common_pixel_count>0)].copy()
base['reference_x']=np.floor(base.x_center_m/500).astype(int)
base['reference_y']=np.floor(base.y_center_m/500).astype(int)
assert (base.reference_x==base.x_index).all() and (base.reference_y==base.y_index).all()
def probs(x,k):
 vals=np.sort(x)[::-1];cut=vals[k-1];a=x>cut;b=x==cut
 return a.astype(float)+b.astype(float)*(k-int(a.sum()))/int(b.sum())
rows=[];qual=[]
for event in E:
 e=base[base.event_id.eq(event)].copy()
 qual.append({'event_id':event,'primary_strict_cells':len(d[d.event_id.eq(event)]),
              'four_chain_strict_cells':len(e),'accepted_fraction':len(e)/len(d[d.event_id.eq(event)]),
              'four_chain_pixels_accepted':int(e.four_chain_common_pixel_count.sum())})
 for scale in SCALES:
  if not len(e):continue
  e['ux']=np.floor(e.x_center_m/scale).astype(np.int64);e['uy']=np.floor(e.y_center_m/scale).astype(np.int64)
  columns=['four_chain_common_pixel_count']+[f'{p}_{s}_water_pixel_count' for p in PRODUCTS for s in ['s30','l30']]
  u=e.groupby(['ux','uy'],as_index=False,sort=True)[columns].sum(); n=len(u);k=max(1,math.ceil(.2*n))
  assert (u.four_chain_common_pixel_count>0).all()
  for p in PRODUCTS:
   s=u[f'{p}_s30_water_pixel_count'].to_numpy()/u.four_chain_common_pixel_count.to_numpy()
   l=u[f'{p}_l30_water_pixel_count'].to_numpy()/u.four_chain_common_pixel_count.to_numpy()
   x,y=u.ux.to_numpy(),u.uy.to_numpy()
   ss=set(zip(x[np.lexsort((y,x,-s))[:k]],y[np.lexsort((y,x,-s))[:k]]))
   ll=set(zip(x[np.lexsort((y,x,-l))[:k]],y[np.lexsort((y,x,-l))[:k]]))
   rho=float(spearmanr(s,l).statistic) if np.unique(s).size>1 and np.unique(l).size>1 else np.nan
   tau=float(kendalltau(s,l,variant='b').statistic) if np.unique(s).size>1 and np.unique(l).size>1 else np.nan
   rows.append(dict(event_id=event,scale_m=scale,product=p,n_units=n,k=k,
                    coordinate_topk_overlap=len(ss&ll)/k,
                    independent_cutoff_ties_expected_overlap=(probs(s,k)*probs(l,k)).sum()/k,
                    spearman=rho,kendall_tau_b=tau,
                    fraction_zero_s30=float(np.mean(s==0)),fraction_zero_l30=float(np.mean(l==0)),
                    eligible_for_primary_min20=n>=20))
metrics=pd.DataFrame(rows);status=pd.DataFrame(qual)
status['hls_asset_status']=['L30 requests incomplete; partial coverage','legacy cache reused; asset resolution must be audited','L30 unavailable; no common cells','both sensor asset sets resolved','both sensor asset sets resolved']
status.to_csv(OUT/'primary_four_chain_event_coverage.csv',index=False)
metrics.to_csv(OUT/'primary_common_four_chain_event_metrics.csv',index=False,float_format='%.12g')
print(status.to_string(index=False))
print('\n500 m and 10 km:')
print(metrics[metrics.scale_m.isin([500,10000])].to_string(index=False))
manifest={'input_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'algorithms':PRODUCTS,
'events':E,'grid_scales_m':SCALES,'budget':0.2,'tie_conventions':['coordinate_order','analytical_expectation_independent_cutoff_ties'],
'qualification':'four chain pixel intersection >=95% eligible pixels in previously primary strict 500 m cells',
'warning':'Four-chain common mask follows archived builder; per-pixel masks are not retained in the output. Minnesota partial and Wisconsin provenance requires review; no South Dakota L30. Not an independent accuracy assessment.',
'water_thresholds':'MNDWI > 0 and AWEI shadow > 0; DSWx published classification; Otsu not included'}
(OUT/'analysis_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')

