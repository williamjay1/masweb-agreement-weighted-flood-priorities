from pathlib import Path
import argparse,json
from datetime import datetime,timezone
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point,shape
from shapely.prepared import prep
p=argparse.ArgumentParser(description='Recompute geometric overlap from preserved official catalog snapshots; this is not valid pixel coverage or a flood classification.')
p.add_argument('--catalog-dir',type=Path,required=True)
p.add_argument('--points',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();df=pd.read_csv(a.points)
if len(df)!=5661:raise ValueError('Expected the frozen 5,661-point original optical common domain')
lon,lat=Transformer.from_crs(5070,4326,always_xy=True).transform(df.x.to_numpy(),df.y.to_numpy());points=[Point(x,y) for x,y in zip(lon,lat)]
rows=[];l30=datetime(2025,5,30,16,48,7,tzinfo=timezone.utc)
for name in ['copernicus','asf']:
 j=json.loads((a.catalog_dir/(name+'_grd_20250520_20250610.json')).read_text(encoding='utf8'))
 for item in j['features']:
  q=item['properties'];dt=q.get('datetime',q.get('startTime'));geom=prep(shape(item['geometry']));mask=[geom.covers(pt) for pt in points]
  rows.append({'catalogue':name,'datetime_utc':dt,'hours_from_l30':(datetime.fromisoformat(dt.replace('Z','+00:00'))-l30).total_seconds()/3600,'platform':q.get('platform'),'scene':item.get('id',q.get('sceneName')),'geometry_centres':sum(mask),'geometry_centres_s30_water':int(df.loc[mask,'s30'].sum()),'geometry_centres_l30_water':int(df.loc[mask,'l30'].sum())})
a.output.parent.mkdir(parents=True,exist_ok=True)
if a.output.exists():raise FileExistsError(a.output)
pd.DataFrame(rows).to_csv(a.output,index=False)
print('Wrote',a.output,'with',len(rows),'scene records')
