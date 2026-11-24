import concurrent.futures, datetime, hashlib, json, pathlib, xml.etree.ElementTree as ET
import requests
from shapely.geometry import box, shape

OUT = pathlib.Path('external/analysis/Geocarto_R2_20261115/missouri_neartime_viirs_followup_20261115/missouri_new_validation')
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
RAW = pathlib.Path('external/data/Geocarto_R2_20261115/raw/missouri_alos2_adjacent_frames') / stamp
RAW.mkdir(parents=True, exist_ok=False)
base = 'https://jaxaalos2.s3.us-west-2.amazonaws.com/'
ns = {'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
domain=box(-94.1241,36.4828,-92.5184,37.8490)
listing=[]; keys=[]; errors=[]
for orbit in [59411-207*n for n in range(1,11)]:
    token=None; page=0
    while True:
        params={'list-type':'2','prefix':f'palsar2/L2.2/2025/ALOS2{orbit}','max-keys':1000}
        if token: params['continuation-token']=token
        resp=requests.get(base,params=params,timeout=60); resp.raise_for_status()
        b=resp.content; f=RAW/f'{orbit}_{page:02}.xml'; f.write_bytes(b)
        root=ET.fromstring(b); found=[e.text for e in root.findall('s:Contents/s:Key',ns)]
        keys.extend(k for k in found if k.endswith('.json'))
        listing.append({'orbit':orbit,'page':page,'objects':len(found),'sha256':hashlib.sha256(b).hexdigest()})
        if root.find('s:IsTruncated',ns).text == 'false': break
        token=root.find('s:NextContinuationToken',ns).text; page+=1
    print(orbit,flush=True)
def get(k):
    try:
        r=requests.get(base+k,timeout=60);r.raise_for_status();b=r.content;j=json.loads(b)
        f=RAW/pathlib.PurePosixPath(k).name; f.write_bytes(b)
        g=shape(j['geometry'])
        return {'key':k,'id':j['id'],'datetime':j['properties']['datetime'], 'bbox':j['bbox'], 'intersects':g.intersects(domain), 'sha256':hashlib.sha256(b).hexdigest()}
    except Exception as e:return {'key':k,'error':repr(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool: rows=list(pool.map(get,keys))
result={'query_utc':stamp,'bbox':list(domain.bounds),'raw':str(RAW),'listing':listing,'total_json':len(keys),'errors':[r for r in rows if 'error' in r], 'matches':[r for r in rows if r.get('intersects')], 'all':rows}
(OUT/f'alos_adjacent_{stamp}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'raw':str(RAW),'metadata_count':len(keys),'errors':result['errors'],'matches':result['matches']},indent=2),flush=True)
