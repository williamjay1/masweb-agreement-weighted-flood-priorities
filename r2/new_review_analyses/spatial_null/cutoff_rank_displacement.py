"""Post hoc rank displacement at the 20% selection boundary."""
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2]
f=ROOT/'inputs/primary_500m_cells.parquet'
ref=ROOT/'inputs/historical_hls_sar_per_event_metrics.csv'
out=Path(__file__).resolve().parent
ids=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
fields=['strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count']
d=pd.read_parquet(f,columns=['event_id','x_index','y_index','strict_common_valid_coverage']+fields)
d=d[d.event_id.isin(ids)&d.strict_common_valid_coverage.ge(.95)&d.strict_common_valid_pixel_count.gt(0)]
previous=pd.read_csv(ref)
rows=[]
for event,g in d.groupby('event_id',sort=True):
 for scale in [.5,10.]:
  z=g.copy();z['gx']=z.x_index//int(scale*2);z['gy']=z.y_index//int(scale*2)
  z=z.groupby(['gx','gy'],sort=True,as_index=False)[fields].sum()
  n=len(z);k=int(np.ceil(.2*n))
  x=z.gx.to_numpy();y=z.gy.to_numpy();den=z[fields[0]].to_numpy()
  a=z[fields[1]].to_numpy()/den;b=z[fields[2]].to_numpy()/den
  # Matches original descending score then x, then y order.
  ia=np.lexsort((y,x,-a));ib=np.lexsort((y,x,-b))
  ra=np.empty(n,int);rb=np.empty(n,int);ra[ia]=np.arange(1,n+1);rb[ib]=np.arange(1,n+1)
  disagreement=(ra<=k)!=(rb<=k)
  near=np.minimum(np.abs(ra-k),np.abs(rb-k))/n
  disp=np.abs(ra-rb)/n
  overlap=np.intersect1d(ia[:k],ib[:k]).size/k
  r=previous[(previous.event_id==event)&np.isclose(previous.scale_km,scale)&np.isclose(previous.budget,.2)]
  assert len(r)==1 and int(r.iloc[0].n_cells)==n and int(r.iloc[0].k)==k
  assert np.isclose(overlap,r.iloc[0].topk_overlap,atol=1e-12),(event,scale,overlap,r.iloc[0].topk_overlap)
  rows.append({'event_id':event,'scale_km':scale,'n_units':n,'k':k,'overlap':overlap,'discordant_unit_count':int(disagreement.sum()),'discordant_fraction_near_boundary_10pct':float((near[disagreement]<=.1).mean()) if disagreement.any() else np.nan,'discordant_median_absolute_rank_displacement_fraction':float(np.median(disp[disagreement])) if disagreement.any() else np.nan,'all_median_absolute_rank_displacement_fraction':float(np.median(disp))})
result=pd.DataFrame(rows);result.to_csv(out/'cutoff_rank_displacement.csv',index=False)
print(result.to_string(index=False))

