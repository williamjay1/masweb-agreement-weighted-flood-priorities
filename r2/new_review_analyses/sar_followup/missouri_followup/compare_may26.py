from pathlib import Path
import argparse,json,hashlib
import numpy as np,pandas as pd,rasterio
from rasterio.warp import reproject,Resampling
p=argparse.ArgumentParser();p.add_argument('--derived-root',type=Path,required=True);p.add_argument('--cells',type=Path,required=True);p.add_argument('--gfm',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
e='N2025_202615_MISSOURI';sel=pd.read_parquet(a.cells);sel=sel[(sel.event_id==e)&sel.strict_qualified].copy();assert len(sel)==562
sp=a.derived_root/'blind_opera_pair_states'/e/(e+'_S30_state_EPSG5070_30m.tif');lp=a.derived_root/'blind_opera_pair_states'/e/(e+'_L30_state_EPSG5070_30m.tif');ep=a.derived_root/'blind_eligibility'/e/(e+'_lagged_eligibility_EPSG5070_30m.tif')
with rasterio.open(sp) as s,rasterio.open(lp) as l,rasterio.open(ep) as ag:
 assert s.transform==l.transform==ag.transform and s.shape==l.shape==ag.shape and s.crs==l.crs==ag.crs
 tr,crs,shape=s.transform,s.crs,s.shape;sg=s.read(2);sq=s.read(4);lg=l.read(2);lq=l.read(4);elig=ag.read(6)==1
 ok=elig&(sg<=1)&(lg<=1)&((sq&127)==0)&((lq&127)==0)&((sq&128)!=0)&((lq&128)!=0)
 rr,cc=np.where(ok);xi=np.floor((tr.c+(cc+.5)*tr.a)/500).astype('int32');yi=np.floor((tr.f+(rr+.5)*tr.e)/500).astype('int32')
 pix=pd.DataFrame({'r':rr,'c':cc,'x_index':xi,'y_index':yi,'s30':sg[rr,cc],'l30':lg[rr,cc]}).merge(sel[['x_index','y_index','strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count']],on=['x_index','y_index'],how='inner',validate='many_to_one')
 check=pix.groupby(['x_index','y_index']).agg(n=('s30','size'),s=('s30','sum'),l=('l30','sum')).reset_index().merge(sel,on=['x_index','y_index'],validate='one_to_one')
 assert len(check)==562 and (check.n==check.strict_common_valid_pixel_count).all() and (check.s==check.strict_s30_water_pixel_count).all() and (check.l==check.strict_l30_water_pixel_count).all(); assert len(pix)==5661
with rasterio.open(a.gfm) as ds:
 assert ds.nodata==255
 dst=np.full(shape,255,dtype='uint8');reproject(source=rasterio.band(ds,1),destination=dst,src_transform=ds.transform,src_crs=ds.crs,src_nodata=255,dst_transform=tr,dst_crs=crs,dst_nodata=255,resampling=Resampling.nearest,num_threads=2);v=dst[pix.r.to_numpy(),pix.c.to_numpy()];assert np.isin(v,[0,1,255]).all();pix['radar']=v
z=pix[pix.radar!=255].copy(); print('total',len(pix),'joint',len(z),'cells',z[['x_index','y_index']].drop_duplicates().shape[0],'positive S30',z.s30.sum(),'L30',z.l30.sum(),'radar',z.radar.sum())
rows=[]
for sensor in ('s30','l30'):
 for optical in [0,1]:
  for radar in [0,1]:rows.append({'sensor':sensor,'optical':optical,'radar':radar,'pixels':int(((z[sensor]==optical)&(z.radar==radar)).sum())})
pd.DataFrame(rows).to_csv(a.out/'missouri_may26_confusion.csv',index=False)
z.to_csv(a.out/'missouri_may26_common_pixels.csv',index=False)
(a.out/'missouri_may26_manifest.json').write_text(json.dumps({'source':'Copernicus GFM observed water','processing_version':'GFM v4.0.0 NRT','source_url':'https://data.eodc.eu/collections/GFM_LAYERS/obswater_mask/NA020M/2025/05/26/ENSEMBLE_OBSWATER_20250526T002030_VV_NA020M_E084N030T3.tif','tile':a.gfm.name,'sha256':hashlib.sha256(a.gfm.read_bytes()).hexdigest(),'radar_time_utc':'2025-05-26T00:20:30Z','optical_time_utc':['2025-05-30T16:48:07Z','2025-05-30T16:58:49Z'],'accepted_cells':562,'accepted_optical_common_pixels':len(pix),'joint_valid':len(z),'joint_cells':int(z[['x_index','y_index']].drop_duplicates().shape[0]),'radar_water':int(z.radar.sum()),'optical_s30_water':int(z.s30.sum()),'optical_l30_water':int(z.l30.sum()),'limits':'post hoc, 4.7 day gap, only small fraction of original domain; no radar water positives, not a useful independent accuracy test; radar product ancillary data and time mismatch'},indent=2),encoding='utf8')
