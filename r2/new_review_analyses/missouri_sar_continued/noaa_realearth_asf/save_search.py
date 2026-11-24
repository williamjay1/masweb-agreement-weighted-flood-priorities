from pathlib import Path
from datetime import datetime,timezone
import requests,json,hashlib
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
raw=Path('external/data/Geocarto_R2_20261115/raw/missouri_realearth_asf_search')/stamp
raw.mkdir(parents=True,exist_ok=False)
out=Path('external/analysis/Geocarto_R2_20261115/missouri_followup_20261115/sar_search_evidence')
ids=['C-band-HH-HV-dual-pol','C-band-HH-HV-dual-pol-m','C-band-VV-VH-dual-pol','C-band-VV-VH-dual-pol-m']
records=[]
def save(label,url,params=None):
 r=requests.get(url,params=params,timeout=80);r.raise_for_status();p=raw/(label+'.json' if 'json' in r.headers.get('content-type','').lower() else label+'.txt');p.write_bytes(r.content)
 records.append({'label':label,'request_url':r.url,'http_status':r.status_code,'raw_file':str(p),'sha256':hashlib.sha256(r.content).hexdigest(),'bytes':len(r.content)});return r
for pid in ids:save('product_'+pid,'https://realearth.ssec.wisc.edu/api/products',{'products':pid})
save('vvvh_20250602_scene','https://realearth.ssec.wisc.edu/api/shapes',{'products':'C-band-VV-VH-dual-pol-m_20250602_091402'})
save('gmu_archive_site_js','https://jpssflood.gmu.edu/js/site.js')
p={'platform':'Sentinel-1','processingLevel':'GRD_HD','intersectsWith':'POLYGON((-94.1241 36.4828,-92.5184 36.4828,-92.5184 37.8490,-94.1241 37.8490,-94.1241 36.4828))','start':'2025-05-23T00:00:00Z','end':'2025-06-06T23:59:59Z','output':'geojson'}
r=save('asf_s1_grd_bbox','https://api.daac.asf.alaska.edu/services/search/param',p)
report={'utc':stamp,'raw_root':str(raw),'requests':records}
(out/'source_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
summary=[]
for pid in ids:
 item=json.loads((raw/('product_'+pid+'.json')).read_text(encoding='utf8'))[0]
 found=[x for x in item['times'] if '20250520'<=x[:8]<='20250610'];summary.append(f'- `{pid}`: {len(found)} timestamps: {found}')
shape=json.loads((raw/'vvvh_20250602_scene.json').read_text(encoding='utf8'))['features'][0]['properties']
scenes=r.json()['features']
text='''# Missouri NOAA RealEarth and ASF bounded search

Post hoc search for the accepted-domain bounding rectangle W -94.1241, S 36.4828, E -92.5184, N 37.8490. Research optical acquisitions were 2025-05-30 UTC. The SSEC flood-product page describes the four C-band experimental products as possibly derived from Sentinel-1, RCM, or Radarsat-2: https://www.ssec.wisc.edu/flood-map-demo/flood-products/. The official API uses exact product time matching and serves product metadata and feature geometries: https://realearth.ssec.wisc.edu/doc/api.php.

## RealEarth product time inventory

Global product times from four `api/products` JSON responses, filtered inclusively to 2025-05-20 through 2025-06-10:

'''+ '\n'.join(summary)+f'''

The sole VV/VH product record is Sentinel-1A, scene `{shape['PRODUCTNAME']}`, centred at {shape['CENTERLAT']}, {shape['CENTERLON']}; this lies in South America, outside Missouri. Its shape response states `ACCESSURL: {shape['ACCESSURL']}`. These results are limited to the four queried layers and this date interval; they do not rule out other archives or private products. No applicable SAR raster was downloaded or compared. Metadata may not constitute a comprehensive inventory of all sensor archives.

The NOAA/GMU public archive's own client JavaScript exposes product choices VIIRS 375-m, VIIRS 375-m 5-Day, ABI 1-km, AHI 1-km, Joint VIIRS/ABI and Joint VIIRS/AHI, with no SAR option. This describes that archive's displayed options, not the existence of products elsewhere: https://jpssflood.gmu.edu/ and https://jpssflood.gmu.edu/js/site.js.

## ASF Sentinel-1 GRD catalog

ASF public search returned {len(scenes)} GRD_HD records intersecting the rectangle from 2025-05-23 00:00:00 to 2025-06-06 23:59:59 UTC:

'''+''.join('- `'+f['properties']['sceneName']+'`, '+f['properties']['startTime']+'\n' for f in scenes)+'''
These two Sentinel-1A scenes are those already identified on 26 May. A footprint intersection does not establish usable pixels. This search checks ASF Sentinel-1 GRD_HD for this rectangle and time window only; it is not a search of all satellites, processing levels or commercial holdings. Official endpoint: https://api.daac.asf.alaska.edu/services/search/param.

`source_manifest.json` supplies exact request URLs, HTTP status, SHA-256, and read-only source snapshot paths. All snapshots were saved as newly named files on F; this report and manifest are on D. No credentials were used or recorded.
'''
(out/'NOAA_REALEARTH_ASF_SEARCH.md').write_text(text,encoding='utf8')
print('raw',raw);print(text[:3500])
