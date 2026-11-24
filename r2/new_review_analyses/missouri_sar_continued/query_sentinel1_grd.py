from pathlib import Path
import requests,json,hashlib
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point,shape
from shapely.prepared import prep
from datetime import datetime,timezone
bbox='-94.1241,36.4828,-92.5184,37.8490'; bboxw='POLYGON((-94.1241 36.4828,-92.5184 36.4828,-92.5184 37.849,-94.1241 37.849,-94.1241 36.4828))'
raw=Path('external/data/Geocarto_R2_20261115/raw/missouri_sar_continue_catalog_20261115');raw.mkdir(parents=True,exist_ok=True)
out=Path('external/analysis/Geocarto_R2_20261115/missouri_sar_continued_20261115/raw_search');out.mkdir(parents=True,exist_ok=True)
configs=[('copernicus','https://stac.dataspace.copernicus.eu/v1/search',{'collections':'sentinel-1-grd','bbox':bbox,'datetime':'2025-05-20T00:00:00Z/2025-06-10T23:59:59Z','limit':100}),('asf','https://api.daac.asf.alaska.edu/services/search/param',{'dataset':'SENTINEL-1','processingLevel':'GRD_HD','intersectsWith':bboxw,'start':'2025-05-20T00:00:00Z','end':'2025-06-10T23:59:59Z','output':'geojson','maxResults':'500'})]
df=pd.read_csv('external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv');assert len(df)==5661
lon,lat=Transformer.from_crs(5070,4326,always_xy=True).transform(df.x.to_numpy(),df.y.to_numpy());pts=[Point(x,y) for x,y in zip(lon,lat)]
rows=[]
for name,url,params in configs:
 r=requests.get(url,params=params,timeout=90);r.raise_for_status();j=r.json();f=raw/(name+'_grd_20250520_20250610.json');assert not f.exists(),f;f.write_bytes(r.content)
 print(name,'snapshot',f,'n',len(j['features']),'sha256',hashlib.sha256(r.content).hexdigest(),flush=True)
 print('next', [(l.get('rel'),l.get('href')) for l in j.get('links',[]) if l.get('rel')=='next'])
 for item in j['features']:
  p=item['properties'];dt=p.get('datetime',p.get('startTime'));geom=prep(shape(item['geometry']));mask=[geom.covers(pt) for pt in pts]
  id=item.get('id',p.get('sceneName'));platform=p.get('platform');dt2=datetime.fromisoformat(dt.replace('Z','+00:00'));l30=datetime(2025,5,30,16,48,7,tzinfo=timezone.utc)
  rows.append({'catalogue':name,'datetime_utc':dt,'hours_from_l30':(dt2-l30).total_seconds()/3600,'platform':platform,'scene':id,'geometry_centres':sum(mask),'geometry_centres_s30_water':int(df.loc[mask,'s30'].sum()),'geometry_centres_l30_water':int(df.loc[mask,'l30'].sum())})
d=pd.DataFrame(rows);d.to_csv(out/'sentinel1_grd_catalog_footprint_screen.csv',index=False);print(d.to_string(index=False));
