import requests, json, pathlib, hashlib, datetime, collections
run = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
raw = pathlib.Path(r'external/data/Geocarto_R2_20261115/raw/missouri_ground_obs_new_20261115') / run
out = pathlib.Path(r'external/analysis/Geocarto_R2_20261115/missouri_ground_obs_new_20261115')
raw.mkdir(parents=True, exist_ok=False)
bbox=[-94.1241,36.4828,-92.5184,37.8490]
search='https://planetarycomputer.microsoft.com/api/stac/v1/search'
reqs=[('naip_near.json', 'POST', search, {'collections':['naip'],'bbox':bbox,'datetime':'2025-05-20T00:00:00Z/2025-06-05T23:59:59Z','limit':500}),('naip_2025.json', 'POST', search, {'collections':['naip'],'bbox':bbox,'datetime':'2025-01-01T00:00:00Z/2025-12-31T23:59:59Z','limit':500}),('usgs_mo_high_water_marks.json','GET','https://api.waterdata.usgs.gov/stnservices/hwms/filteredhwms/',{'states':'MO'}),('usgs_events.json','GET','https://api.waterdata.usgs.gov/stnservices/events/',{})]
res={}; meta=[]
for name,method,url,p in reqs:
 r=requests.post(url,json=p,timeout=60) if method=='POST' else requests.get(url,params=p,timeout=60)
 r.raise_for_status(); obj=r.json(); data=r.content
 (raw / name).write_bytes(data); res[name]=obj
 meta.append({'file':str(raw/name),'method':method,'url':r.url,'request':p,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'status':r.status_code})
a=res['naip_2025.json']; assert all(l['rel']!='next' for l in a.get('links',[])), 'Pagination requires continuation'
n=res['naip_near.json']; assert all(l['rel']!='next' for l in n.get('links',[])), 'Pagination requires continuation'
h=res['usgs_mo_high_water_marks.json']; matched=[x for x in h if x.get('latitude') is not None and x.get('longitude') is not None and bbox[0]<=x['longitude']<=bbox[2] and bbox[1]<=x['latitude']<=bbox[3]]
summary={'retrieved_utc':run,'bbox':bbox,'naip_near_returned':len(n['features']),'naip_2025_returned':len(a['features']),'naip_2025_states':dict(collections.Counter(x['id'].split('_')[0] for x in a['features'])),'naip_2025_dates':dict(collections.Counter(x['properties']['datetime'][:10] for x in a['features'])),'usgs_state_marks':len(h),'usgs_bbox_marks':len(matched),'usgs_2025_event_names':sorted(set(x['event_name'] for x in h if '2025' in str(x.get('event_name')))),'response_files':meta}
file=out / ('screen_summary_'+run+'.json'); file.write_text(json.dumps(summary,indent=2),encoding='utf-8'); print(json.dumps(summary,ensure_ascii=False,indent=2))
