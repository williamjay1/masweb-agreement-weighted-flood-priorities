from pathlib import Path
import argparse, json, hashlib
import pyarrow.dataset as ds
from pyproj import Transformer
import pandas as pd,numpy as np,rasterio
p=argparse.ArgumentParser();p.add_argument('--tile',type=Path,required=True);p.add_argument('--cells',type=Path,required=True);p.add_argument('--derived-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
e='N2023_179829_WISCONSIN';s=pd.read_parquet(a.cells);s=s[(s.event_id==e)&s.strict_qualified].copy();assert len(s)==221
tr=Transformer.from_crs(5070,4326,always_xy=True);lon,lat=tr.transform((s.x_index+.5)*500,(s.y_index+.5)*500)
f=(ds.field('year')==2023)&(ds.field('month')==4)&(ds.field('day')>=7)&(ds.field('day')<=22)&(ds.field('lat')>=float(min(lat)-.015))&(ds.field('lat')<=float(max(lat)+.015))&(ds.field('lon')>=float(min(lon)-.02))&(ds.field('lon')<=float(max(lon)+.02))
d=ds.dataset(a.tile,format='parquet').to_table(filter=f,columns=['year','month','day','lat','lon','filename','edge_false_positives']).to_pandas();x,y=Transformer.from_crs(4326,5070,always_xy=True).transform(d.lon.to_numpy(),d.lat.to_numpy());d['x']=x;d['y']=y;d['x_index']=np.floor(x/500).astype(int);d['y_index']=np.floor(y/500).astype(int);z=d.merge(s[['x_index','y_index']],on=['x_index','y_index'],how='inner',validate='many_to_one')
sp=a.derived_root/'blind_opera_pair_states'/e/(e+'_S30_state_EPSG5070_30m.tif');lp=a.derived_root/'blind_opera_pair_states'/e/(e+'_L30_state_EPSG5070_30m.tif');ep=a.derived_root/'blind_eligibility'/e/(e+'_lagged_eligibility_EPSG5070_30m.tif')
with rasterio.open(sp) as ssrc,rasterio.open(lp) as lsrc,rasterio.open(ep) as esrc:
 assert ssrc.transform==lsrc.transform==esrc.transform and ssrc.crs==lsrc.crs==esrc.crs
 pts=list(zip(z.x,z.y));S=np.array(list(ssrc.sample(pts,indexes=[2,4])));L=np.array(list(lsrc.sample(pts,indexes=[2,4])));E=np.array(list(esrc.sample(pts,indexes=[6]))).ravel();z['s30_state']=S[:,0];z['s30_qa']=S[:,1];z['l30_state']=L[:,0];z['l30_qa']=L[:,1];z['eligible_band6']=E;z['optical_common_valid']=(E==1)&(S[:,0]<=1)&(L[:,0]<=1)&((S[:,1]&127)==0)&((L[:,1]&127)==0)&((S[:,1]&128)!=0)&((L[:,1]&128)!=0)
z.to_csv(a.output/'wisconsin_detections_in_accepted_cells.csv',index=False);print('Bounding box positive detections:',len(d),'in accepted cells:',len(z));print(z[['day','lat','lon','filename','s30_state','l30_state','eligible_band6','optical_common_valid']].to_string(index=False))
print('Dates are detection days, not proof of all valid radar observations. No nondetections inferred. Source sha256:',hashlib.sha256(a.tile.read_bytes()).hexdigest())
