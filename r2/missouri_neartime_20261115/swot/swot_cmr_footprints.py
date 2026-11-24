import concurrent.futures as futures
import datetime as dt
import json
from pathlib import Path
import requests
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, Polygon, box, mapping
from shapely.ops import unary_union
from lxml import etree

raw = Path('external/data/Geocarto_R2_20261115/raw/missouri_swot_metadata_20261115')
out = Path('external/analysis/Geocarto_R2_20261115/missouri_swot_new_footprints_20261115')
raw.mkdir(parents=True, exist_ok=True)
out.mkdir(parents=True, exist_ok=True)
params = {'collection_concept_id':'C3233944986-POCLOUD', 'bounding_box':'-94.1241,36.4828,-92.5184,37.8490', 'temporal':'2025-05-26T00:00:00Z,2025-06-04T00:00:00Z', 'page_size':200}
r = requests.get('https://cmr.earthdata.nasa.gov/search/granules.umm_json',params=params,timeout=90); r.raise_for_status()
with (raw/'cmr_umm.json').open('xb') as f: f.write(r.content)
with (out/'query.json').open('x',encoding='utf8') as f: json.dump({'request_url':r.url,'retrieved_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'cmr_hits':r.headers.get('CMR-Hits')},f,indent=2)
items=r.json()['items']

def get_iso(item):
 u=item['umm']; name=u['GranuleUR']; link=next(a['URL'] for a in u['RelatedUrls'] if a['URL'].startswith('https:') and a['URL'].endswith('.nc.iso.xml'))
 q=requests.get(link,timeout=90); q.raise_for_status()
 with (raw/(name+'.nc.iso.xml')).open('xb') as f: f.write(q.content)
 doc=etree.fromstring(q.content)
 ns={'gml':'http://www.opengis.net/gml/3.2'}
 ps=doc.xpath('//gml:Polygon/gml:exterior//gml:posList/text()',namespaces=ns)
 if len(ps)!=1: raise ValueError((name,ps))
 v=list(map(float,ps[0].split())); poly=Polygon([(v[i+1],v[i]) for i in range(0,len(v),2)])
 if not poly.is_valid: raise ValueError(name)
 return name,poly,link

with futures.ThreadPoolExecutor(max_workers=8) as pool: met=list(pool.map(get_iso,items))
poly_by_name={name:(p,link) for name,p,link in met}
d=pd.read_csv('external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv')
t=Transformer.from_crs(5070,4326,always_xy=True); lon,lat=t.transform(d.x.to_numpy(),d.y.to_numpy()); points=[Point(x,y) for x,y in zip(lon,lat)]
region=box(-94.1241,36.4828,-92.5184,37.8490)
rows=[]; features=[]; passes={}
for item in items:
 u=item['umm']; name=u['GranuleUR']; p,link=poly_by_name[name]; start=u['TemporalExtent']['RangeDateTime']['BeginningDateTime']; pass_id='_'.join(name.split('_')[4:6]); covered=[pt for pt in points if p.covers(pt)]
 diff=(dt.datetime.fromisoformat('2025-05-30T16:58:49+00:00')-dt.datetime.fromisoformat(start.replace('Z','+00:00'))).total_seconds()/3600
 rows.append({'granule':name,'pass_id':pass_id,'start_utc':start,'hours_before_s30':diff,'nominal_polygon_sample_points':len(covered),'bbox_intersection':p.intersects(region),'iso_url':link})
 features.append({'type':'Feature','geometry':mapping(p),'properties':{'granule':name,'start_utc':start}}); passes.setdefault(pass_id,[]).append(p)
pd.DataFrame(rows).to_csv(out/'granule_footprint_intersections.csv',index=False)
summ=[]
for k,polys in passes.items():
 p=unary_union(polys); n=sum(p.covers(pt) for pt in points); subset=[r for r in rows if r['pass_id']==k]
 summ.append({'pass_id':k,'start_utc_min':min(x['start_utc'] for x in subset),'start_utc_max':max(x['start_utc'] for x in subset),'granules':len(subset),'nominal_polygon_sample_points_union':n,'fraction_of_5661':n/len(points)})
pd.DataFrame(summ).to_csv(out/'pass_footprint_intersections.csv',index=False)
with (out/'swot_nominal_footprints.geojson').open('x',encoding='utf8') as f:json.dump({'type':'FeatureCollection','features':features},f)
print(pd.DataFrame(summ).to_string(index=False)); print('n granules',len(rows),'n points',len(points))
