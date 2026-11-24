import hashlib, json, pathlib
import pandas as pd
from pyproj import Transformer
from shapely.geometry import box, shape

out=pathlib.Path('external/analysis/Geocarto_R2_20261115/missouri_neartime_viirs_followup_20261115/missouri_new_validation')
meta=json.loads((out/'alos_adjacent_20261114T233708Z.json').read_text(encoding='utf-8'))
raw=pathlib.Path(meta['raw']); domain=box(*meta['bbox']); issues=[]; matches=[]; bounds=[]
for row in meta['listing']:
    b=(raw/f"{row['orbit']}_{row['page']:02}.xml").read_bytes()
    if hashlib.sha256(b).hexdigest()!=row['sha256']:issues.append('listing hash mismatch')
for row in meta['all']:
    if 'error' in row:
        issues.append(row);continue
    b=(raw/pathlib.PurePosixPath(row['key']).name).read_bytes()
    if hashlib.sha256(b).hexdigest()!=row['sha256']:issues.append('item hash mismatch: '+row['id'])
    g=shape(json.loads(b)['geometry'])
    if not g.is_valid or g.geom_type!='Polygon':issues.append('invalid geometry: '+row['id'])
    if g.intersects(domain):matches.append(row['id'])
    bounds.append(g.bounds)
samples=pd.read_csv('external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv')
lon,lat=Transformer.from_crs(5070,4326,always_xy=True).transform(samples.x.to_numpy(),samples.y.to_numpy())
minx,miny,maxx,maxy=domain.bounds
inside=(lon>=minx)&(lon<=maxx)&(lat>=miny)&(lat<=maxy)
result={'sample_count':len(samples),'inside_bbox_count':int(inside.sum()),'sample_longitude_range':[float(min(lon)),float(max(lon))], 'sample_latitude_range':[float(min(lat)),float(max(lat))], 'item_count':len(meta['all']),'listing_count':len(meta['listing']),'issues':issues,'geometry_matches':matches}
(out/'verification_retained_search.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
