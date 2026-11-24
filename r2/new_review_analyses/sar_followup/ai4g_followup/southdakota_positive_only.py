from pathlib import Path
import argparse,hashlib,json,re
import pyarrow.dataset as ds
from pyproj import Transformer
import pandas as pd,numpy as np,rasterio
p=argparse.ArgumentParser();p.add_argument('--tiles',nargs='+',type=Path,required=True);p.add_argument('--cells',type=Path,required=True);p.add_argument('--derived-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
e='N2023_180114_SOUTHDAKOTA';s=pd.read_parquet(a.cells);s=s[(s.event_id==e)&s.strict_qualified].copy();assert len(s)==2628
lon,lat=Transformer.from_crs(5070,4326,always_xy=True).transform((s.x_index+.5)*500,(s.y_index+.5)*500)
f=(ds.field('year')==2023)&(ds.field('month')==4)&(ds.field('day')>=3)&(ds.field('day')<=17)&(ds.field('lat')>=float(min(lat)-.015))&(ds.field('lat')<=float(max(lat)+.015))&(ds.field('lon')>=float(min(lon)-.02))&(ds.field('lon')<=float(max(lon)+.02))
frames=[]
for tile in a.tiles:
 d=ds.dataset(tile,format='parquet').to_table(filter=f,columns=['year','month','day','lat','lon','filename','edge_false_positives']).to_pandas();d['source_tile']=tile.name;frames.append(d);print(tile.name,'bbox detections',len(d),flush=True)
d=pd.concat(frames,ignore_index=True);x,y=Transformer.from_crs(4326,5070,always_xy=True).transform(d.lon.to_numpy(),d.lat.to_numpy());d['x']=x;d['y']=y;d['x_index']=np.floor(x/500).astype(int);d['y_index']=np.floor(y/500).astype(int);z=d.merge(s[['x_index','y_index']],on=['x_index','y_index'],how='inner',validate='many_to_one')
sp=a.derived_root/'blind_opera_pair_states'/e/(e+'_S30_state_EPSG5070_30m.tif');lp=a.derived_root/'blind_opera_pair_states'/e/(e+'_L30_state_EPSG5070_30m.tif');ep=a.derived_root/'blind_eligibility'/e/(e+'_lagged_eligibility_EPSG5070_30m.tif')
with rasterio.open(sp) as ssrc,rasterio.open(lp) as lsrc,rasterio.open(ep) as esrc:
 assert ssrc.transform==lsrc.transform==esrc.transform and ssrc.crs==lsrc.crs==esrc.crs
 pts=list(zip(z.x,z.y));S=np.array(list(ssrc.sample(pts,indexes=[2,4])));L=np.array(list(lsrc.sample(pts,indexes=[2,4])));E=np.array(list(esrc.sample(pts,indexes=[6]))).ravel();rr,cc=rasterio.transform.rowcol(ssrc.transform,z.x.to_numpy(),z.y.to_numpy());z['row30']=rr;z['col30']=cc;z['s30_state']=S[:,0];z['s30_qa']=S[:,1];z['l30_state']=L[:,0];z['l30_qa']=L[:,1];z['eligible_band6']=E;z['optical_common_valid']=(E==1)&(S[:,0]<=1)&(L[:,0]<=1)&((S[:,1]&127)==0)&((L[:,1]&127)==0)&((S[:,1]&128)!=0)&((L[:,1]&128)!=0)
z.to_csv(a.output/'southdakota_ai4g_detections_in_accepted_cells.csv',index=False)
v=z[z.optical_common_valid].copy();u=v.drop_duplicates(['day','row30','col30']);print('In accepted 500m cells',len(z),'and on strict optical common-valid 30m domain',len(v),'unique day,30m pixels',len(u));print('point summary',v.groupby(['day','s30_state','l30_state']).size().to_string());print('unique pixel summary',u.groupby(['day','s30_state','l30_state']).size().to_string());print('scene summary',v.groupby(['day','filename']).size().to_string());print('These positive detections do not establish observed radar negatives or a reference confusion matrix.')
manifest={'event':e,'tiles':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in a.tiles},'bbox_detections':len(d),'accepted_cell_detections':len(z),'common_valid_detections':len(v),'unique_day_pixel':len(u),'limitation':'positive detections only; cannot infer valid radar negative pixels, or accuracy, recall, sensitivity or specificity; direct 20m point centres sampled into 30m optical grid; no buffer'};(a.output/'southdakota_ai4g_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
