from pathlib import Path
import json, hashlib
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import shape, Point
from shapely.ops import transform
raw=Path('external/data/Geocarto_R2_20261115/raw/missouri_nws_lsr_search_20261115')
out=Path('external/analysis/Geocarto_R2_20261115/missouri_reference_recheck_20261115/ground_search');out.mkdir(parents=True,exist_ok=True)
source=Path('external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv')
pts=pd.read_csv(source); assert len(pts)==5661
lsr=pd.read_csv(raw/'nws_lsr_missouri_20250522_20250602.csv')
lsr=lsr[lsr.TYPETEXT.str.contains('FLOOD',case=False,na=False)&lsr.LON.between(-94.1241,-92.5184)&lsr.LAT.between(36.4828,37.849)].copy()
t=Transformer.from_crs(4326,5070,always_xy=True); x,y=t.transform(lsr.LON.to_numpy(),lsr.LAT.to_numpy()); lsr['distance_to_nearest_center_m']=cKDTree(pts[['x','y']]).query(list(zip(x,y)))[0]
lsr['hours_before_l30']=(pd.Timestamp('2025-05-30T16:48:07Z')-pd.to_datetime(lsr.VALID,format='%Y%m%d%H%M',utc=True)).dt.total_seconds()/3600
lsr.to_csv(out/'iem_flood_reports_bbox.csv',index=False)
park_data=json.loads((raw/'osm_finley_park_nominatim.json').read_text(encoding='utf8')); matches=[v for v in park_data if v['type']=='park'];assert len(matches)==1
poly=transform(t.transform,shape(matches[0]['geojson'])); dist=[poly.distance(Point(x,y)) for x,y in zip(pts.x,pts.y)]
result={'query':'https://mesonet.agron.iastate.edu/cgi-bin/request/gis/lsr.py?state=MO&sts=2025-05-22T00%3A00Z&ets=2025-06-02T00%3A00Z&fmt=csv','raw_lsr_sha256':hashlib.sha256((raw/'nws_lsr_missouri_20250522_20250602.csv').read_bytes()).hexdigest(),'lsr_flood_bbox_count_including_correction':len(lsr),'unique_valid_lat_lon':len(lsr.drop_duplicates(['VALID','LAT','LON'])),'by_utc_date':lsr.VALID2.str[:10].value_counts().to_dict(),'min_hours_before_l30':float(lsr.hours_before_l30.min()),'min_distance_m':float(lsr.distance_to_nearest_center_m.min()),'park_raw_sha256':hashlib.sha256((raw/'osm_finley_park_nominatim.json').read_bytes()).hexdigest(),'park_query':'https://nominatim.openstreetmap.org/search?q=Finley+River+Park+Ozark+Missouri&format=jsonv2&polygon_geojson=1&limit=10','park_count_centres_inside':sum(d==0 for d in dist),'park_min_distance_m':min(dist),'park_boundary_is_not_drone_footprint':True,'optical_points_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(out/'ground_search_summary.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
