from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd,rasterio
from rasterio.windows import Window
from pyproj import Transformer
P=Path('external/analysis/Geocarto_R2_20261115/missouri_flood_reference_followup_20261115/alos2_aws');R=Path('external/data/Geocarto_R2_20261115/raw/missouri_alos2_aws_followup_20261115'); SRC=Path('external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv');st='ALOS2594110700-250524_WBDR2.2GUA';df=pd.read_csv(SRC);assert len(df)==5661
paths={k:R/(st+'_'+v+'.tif') for k,v in [('hh','HH_SLP'),('hv','HV_SLP'),('mask','MSK')]};d={k:rasterio.open(f) for k,f in paths.items()};base=d['hh'];assert all(z.crs==base.crs and z.shape==base.shape and z.transform==base.transform for z in d.values())
x,y=Transformer.from_crs(5070,base.crs,always_xy=True).transform(df.x.to_numpy(),df.y.to_numpy()); rows,cols=rasterio.transform.rowcol(base.transform,x,y);df['sar_row']=rows;df['sar_col']=cols;df['in_grid']=df.sar_row.between(0,base.height-1)&df.sar_col.between(0,base.width-1)
for k in d:df[k]=np.nan
inside=df[df.in_grid].copy();inside['br']=inside.sar_row//256;inside['bc']=inside.sar_col//256
for (br,bc),q in inside.groupby(['br','bc']):
 w=Window(int(bc)*256,int(br)*256,min(256,base.width-int(bc)*256),min(256,base.height-int(br)*256)); rr=q.sar_row.to_numpy()-int(w.row_off);cc=q.sar_col.to_numpy()-int(w.col_off)
 for k,ds in d.items():
  arr=ds.read(1,window=w);df.loc[q.index,k]=arr[rr,cc]
for ds in d.values():ds.close()
df['valid']=(df['in_grid'] & (df['mask']==1) & (df.hh>0) & (df.hv>0));v=df.valid
for k in ['hh','hv']:df[k+'_db']=np.nan;df.loc[v,k+'_db']=20*np.log10(df.loc[v,k].astype(float))-83
df.to_csv(P/'alos2_point_samples.csv',index=False)
summary={'source':st,'scene_datetime_utc':'2025-05-24T06:09:52.016500Z','source_epsg':32615,'samples_total':len(df),'in_image_rectangle':int(df.in_grid.sum()),'mask_counts_on_grid':{str(k):int(v) for k,v in df[df.in_grid]['mask'].value_counts().sort_index().items()},'mask_1_positive_dualpol':int(v.sum()),'unique_valid_sar_pixels':int(df[v][['sar_row','sar_col']].drop_duplicates().shape[0]),'groups':{}}
for s in [0,1]:
 for l in [0,1]:
  q=df[v & (df.s30==s) & (df.l30==l)];key=f'S{s}L{l}';summary['groups'][key]={'n_centres':len(q),'n_distinct_sar_cells':int(q[['sar_row','sar_col']].drop_duplicates().shape[0])}
  for k in ['hh_db','hv_db']:
   summary['groups'][key][k+'_q25_median_q75']=[float(x) for x in q[k].quantile([.25,.5,.75])] if len(q) else []
(P/'alos2_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8');print(json.dumps(summary,indent=2),flush=True)
