from pathlib import Path
import numpy as np,pandas as pd,math
from scipy.stats import spearmanr
BASE=Path(__file__).resolve().parent
allfixed=pd.read_parquet(BASE/'inputs/hls_index_500m_cells.parquet')
events=['C2_2025_LOWER_OHIO','D3_2024_CENTRAL_INDIANA','D5_2024_NEBRASKA_IOWA']
def probs(x,k):
 cut=np.sort(x)[::-1][k-1];a=x>cut;b=x==cut
 return a.astype(float)+b.astype(float)*(k-a.sum())/b.sum()
rows=[]
for ev in events:
 a=allfixed[allfixed.event_id.eq(ev)].copy();b=pd.read_parquet(BASE/'inputs/otsu_cells'/f'{ev}_hls_index_500m_cells.parquet')
 j=a.merge(b,on=['event_id','x_index','y_index'],validate='one_to_one',suffixes=('_fixed','_otsu'))
 j=j[j.four_chain_strict_qualified_fixed & j.four_chain_strict_qualified_otsu].copy()
 for scale in [500,1000,2000,5000,10000,20000,30000]:
  j['ux']=np.floor(j.x_center_m_fixed/scale).astype(int);j['uy']=np.floor(j.y_center_m_fixed/scale).astype(int)
  columns=[f'{c}_{t}' for c in ['four_chain_common_pixel_count','mndwi_s30_water_pixel_count','mndwi_l30_water_pixel_count'] for t in ['fixed','otsu']]
  units=j.groupby(['ux','uy'],as_index=False,sort=True)[columns].sum();n=len(units);k=max(1,math.ceil(.2*n))
  for t in ['fixed','otsu']:
   den=units['four_chain_common_pixel_count_'+t].to_numpy()
   assert np.all(den>0)
   s=units['mndwi_s30_water_pixel_count_'+t].to_numpy()/den
   l=units['mndwi_l30_water_pixel_count_'+t].to_numpy()/den
   x,y=units.ux.to_numpy(),units.uy.to_numpy()
   os=np.lexsort((y,x,-s))[:k];ol=np.lexsort((y,x,-l))[:k]
   overlap=len(set(os)&set(ol))/k
   rho=float(spearmanr(s,l).statistic) if len(np.unique(s))>1 and len(np.unique(l))>1 else np.nan
   rows.append(dict(event_id=ev,scale_m=scale,method=t,n_units=n,k=k,
      spearman=rho,coordinate_overlap=overlap,
      random_cutoff_expected_overlap=float((probs(s,k)*probs(l,k)).sum()/k),
      zero_fraction_s30=float((s==0).mean()),zero_fraction_l30=float((l==0).mean()),
      domain_note='same 500 m qualifying cells; per-pixel supports not demonstrated identical'))
r=pd.DataFrame(rows);r.to_csv(BASE/'results/otsu_common_cells_event_metrics.csv',index=False,float_format='%.12g')
print(r[r.scale_m.isin([500,10000])].to_string(index=False))

