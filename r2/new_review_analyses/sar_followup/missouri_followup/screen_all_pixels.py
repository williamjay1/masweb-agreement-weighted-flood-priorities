from pathlib import Path
import argparse,json
import numpy as np,pandas as pd,rasterio
from rasterio.warp import reproject,Resampling
P=argparse.ArgumentParser();P.add_argument('--derived-root',type=Path,required=True);P.add_argument('--gfm-root',type=Path,required=True);P.add_argument('--cells',type=Path,required=True);P.add_argument('--screen',type=Path,required=True);P.add_argument('--output',type=Path,required=True);a=P.parse_args()
sel=pd.read_parquet(a.cells);screen=pd.read_csv(a.screen);results=[]
for e,events in screen.groupby('event_id'):
 print('START',e,flush=True); es=sel[(sel.event_id==e)&sel.strict_qualified];root=a.derived_root
 sp=root/'blind_opera_pair_states'/e/(e+'_S30_state_EPSG5070_30m.tif');lp=root/'blind_opera_pair_states'/e/(e+'_L30_state_EPSG5070_30m.tif');ep=root/'blind_eligibility'/e/(e+'_lagged_eligibility_EPSG5070_30m.tif')
 with rasterio.open(sp) as s,rasterio.open(lp) as l,rasterio.open(ep) as ag:
  assert s.transform==l.transform==ag.transform and s.shape==l.shape==ag.shape and s.crs==l.crs==ag.crs
  tr=s.transform;crs=s.crs;shape=s.shape;sg=s.read(2);lg=l.read(2);sq=s.read(4);lq=l.read(4);eligible=ag.read(6)==1
  ok=eligible&(sg<=1)&(lg<=1)&((sq&127)==0)&((lq&127)==0)&((sq&128)!=0)&((lq&128)!=0)
  xx=np.floor((tr.c+(np.arange(shape[1])+.5)*tr.a)/500).astype('int32'); yy=np.floor((tr.f+(np.arange(shape[0])+.5)*tr.e)/500).astype('int32')
  xmin,xmax=int(xx.min()),int(xx.max());ymin,ymax=int(yy.min()),int(yy.max());grid=np.zeros((ymax-ymin+1,xmax-xmin+1),bool)
  ex=es.x_index.to_numpy();ey=es.y_index.to_numpy();valid=(ex>=xmin)&(ex<=xmax)&(ey>=ymin)&(ey<=ymax);grid[ey[valid]-ymin,ex[valid]-xmin]=1
  ok &= grid[yy[:,None]-ymin,xx[None,:]-xmin];rr,cc=np.where(ok);del sg,lg,sq,lq,eligible,ok
  expected=int(es.strict_common_valid_pixel_count.sum());assert len(rr)==expected,(e,len(rr),expected)
 for row in events.itertuples():
  path=a.gfm_root/(row.item_id+'__ensemble_water_extent.tif');dst=np.full(shape,255,dtype='uint8')
  with rasterio.open(path) as ds: reproject(source=rasterio.band(ds,1),destination=dst,src_transform=ds.transform,src_crs=ds.crs,src_nodata=255,dst_transform=tr,dst_crs=crs,dst_nodata=255,resampling=Resampling.nearest,num_threads=2)
  v=dst[rr,cc];results.append({'event_id':e,'item_id':row.item_id,'datetime':row.datetime,'hours_from_first_optical':row.time_delta_hours,'eligible_optical_pixels':len(v),'valid_pixel_count':int((v!=255).sum()),'water_pixel_count':int((v==1).sum()),'valid_fraction':float((v!=255).mean())});del dst,v
  pd.DataFrame(results).to_csv(a.output,index=False);print('DONE',len(results),e,row.item_id,results[-1]['valid_pixel_count'],flush=True)
