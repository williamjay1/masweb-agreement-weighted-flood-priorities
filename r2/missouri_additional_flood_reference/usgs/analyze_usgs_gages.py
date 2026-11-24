from pathlib import Path
import argparse,json,hashlib
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
p=argparse.ArgumentParser(description='Independent gauge context; distances never imply same flood state for fields.')
p.add_argument('--nwis',type=Path,required=True);p.add_argument('--points',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
points=pd.read_csv(a.points);assert len(points)==5661 and len(points[['x','y']].drop_duplicates())==5661
T=cKDTree(points[['x','y']].to_numpy());tr=Transformer.from_crs(4326,5070,always_xy=True)
raw=json.loads(a.nwis.read_text(encoding='utf8')); rows=[]
for ts in raw['value']['timeSeries']:
 s=ts['sourceInfo'];geo=s['geoLocation']['geogLocation'];x,y=tr.transform(geo['longitude'],geo['latitude']);dist,ind=T.query([x,y]);v=pd.DataFrame(ts['values'][0]['value']);v['dateTime']=pd.to_datetime(v['dateTime'],utc=True);v['value']=pd.to_numeric(v['value'],errors='coerce');nd=float(ts['variable']['noDataValue']);v=v[v.value.notna() & (v.value != nd)].copy();event=v[(v.dateTime>=pd.Timestamp('2025-05-23T00:00:00Z'))&(v.dateTime<pd.Timestamp('2025-05-28T00:00:00Z'))]
 near=v[(v.dateTime>=pd.Timestamp('2025-05-30T15:48:07Z'))&(v.dateTime<=pd.Timestamp('2025-05-30T17:48:07Z'))].copy()
 if event.empty or near.empty:continue
 peak=event.sort_values(['value','dateTime'],ascending=[False,True]).iloc[0];near['delta']=(near.dateTime-pd.Timestamp('2025-05-30T16:48:07Z')).abs();near=near.sort_values(['delta','dateTime']).iloc[0]
 rows.append(dict(site=s['siteCode'][0]['value'],name=s['siteName'],latitude=geo['latitude'],longitude=geo['longitude'],nearest_joint_pixel_center_distance_m=dist,event_peak_ft=peak['value'],event_peak_utc=peak.dateTime.isoformat(),event_peak_qualifiers=','.join(peak.qualifiers),near_L30_ft=near['value'],near_L30_utc=near.dateTime.isoformat(),near_L30_qualifiers=','.join(near.qualifiers),difference_ft=peak['value']-near['value']))
df=pd.DataFrame(rows).sort_values(['nearest_joint_pixel_center_distance_m','site']);fn=a.out/'usgs_gages_nearest_joint_domain.csv';
if fn.exists():raise FileExistsError(fn)
df.to_csv(fn,index=False);print('sites with both measurements',len(df));print(df.head(3).to_string(index=False));print('input sha256',hashlib.sha256(a.nwis.read_bytes()).hexdigest())
