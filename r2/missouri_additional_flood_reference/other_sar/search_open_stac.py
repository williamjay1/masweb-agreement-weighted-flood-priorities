import os,json,hashlib,requests,concurrent.futures,urllib.parse,time
from pathlib import Path
from shapely.geometry import shape,box
R=Path('external/data/Geocarto_R2_20261115/raw/missouri_other_sar_stac_20261115');R.mkdir(parents=True,exist_ok=True)
D=Path('external/analysis/Geocarto_R2_20261115/missouri_flood_reference_20261115/other_sar');D.mkdir(parents=True,exist_ok=True)
aoi=box(-94.1241,36.4828,-92.5184,37.8490)
sources={'umbra':'https://s3.us-west-2.amazonaws.com/umbra-open-data-catalog/stac/2025/2025-05/catalog.json','capella':'https://capella-open-data.s3.us-west-2.amazonaws.com/stac/capella-open-data-by-datetime/capella-open-data-2025/capella-open-data-2025-05/catalog.json'}
def get(url):
 for i in range(4):
  try:
   r=requests.get(url,timeout=45);r.raise_for_status(); b=r.content; j=r.json(); n=hashlib.sha256(url.encode()).hexdigest()+'.json'; dest=R/n;
   if dest.exists() and dest.read_bytes()!=b: raise RuntimeError('Existing raw snapshot differs, refuse overwrite: '+str(dest))
   if not dest.exists(): dest.write_bytes(b)
   return (url,j,n,None)
  except Exception as e:
   if i==3:return(url,None,None,str(e))
   time.sleep(i+1)
def batch(urls):
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:return list(pool.map(get,urls))
out={'aoi':list(aoi.bounds),'date_utc':['2025-05-23','2025-05-30'],'sources':{},'errors':[]}
for name,root in sources.items():
 _, month,filename,err=get(root)
 if err:out['errors'].append([root,err]);continue
 days=[urllib.parse.urljoin(root,x['href']) for x in month['links'] if x['rel']=='child' and any(f'2025-05-{d:02d}' in x.get('title','') for d in range(23,31))]
 daydata=batch(days); items=[]
 for u,j,n,e in daydata:
  if e:out['errors'].append([u,e]);continue
  items += [urllib.parse.urljoin(u,x['href']) for x in j['links'] if x['rel']=='item']
 result=batch(items);hits=[]; count=0
 for u,j,n,e in result:
  if e:out['errors'].append([u,e]);continue
  count+=1
  try:
   if shape(j['geometry']).intersects(aoi):hits.append({'id':j['id'],'datetime':j['properties'].get('datetime'),'bbox':j.get('bbox'),'url':u,'snapshot':n,'assets':j.get('assets',{})})
  except Exception as e:out['errors'].append([u,'geometry '+str(e)])
 out['sources'][name]={'month_url':root,'month_snapshot':filename,'daily_catalogs_searched':len(days),'items_expected':len(items),'items_read':count,'matches':hits}
 print(name,'days',len(days),'items',len(items),'read',count,'hits',len(hits),flush=True)
(D/'open_stac_search_results.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('errors',out['errors'])
