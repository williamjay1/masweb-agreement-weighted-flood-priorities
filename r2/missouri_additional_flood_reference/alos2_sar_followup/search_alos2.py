import requests,xml.etree.ElementTree as ET,json,re,pathlib,concurrent.futures,hashlib,datetime,time
from shapely.geometry import box,shape
from shapely.prepared import prep
O=pathlib.Path('external/analysis/Geocarto_R2_20261115/missouri_flood_reference_followup_20261115/alos2_aws');O.mkdir(parents=True,exist_ok=True)
R=pathlib.Path('external/data/Geocarto_R2_20261115/raw/missouri_alos2_aws_followup_20261115');R.mkdir(parents=True,exist_ok=True)
base='https://jaxaalos2.s3.us-west-2.amazonaws.com/';ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'};keys=[];pages=[]
for orbit in ['593','594','595']:
 prefix='palsar2/L2.2/2025/ALOS2'+orbit;token=None;i=0
 while True:
  params={'list-type':'2','prefix':prefix,'max-keys':1000}
  if token:params['continuation-token']=token
  r=requests.get(base,params=params,timeout=60);r.raise_for_status();root=ET.fromstring(r.content)
  f=R/f'list_{orbit}_{i:02}.xml'
  if f.exists() and f.read_bytes()!=r.content:raise RuntimeError('snapshot exists different')
  if not f.exists():f.write_bytes(r.content)
  page=[k.text for k in root.findall('s:Contents/s:Key',ns)];keys.extend(page);pages.append({'prefix':prefix,'page':i,'n':len(page),'sha256':hashlib.sha256(r.content).hexdigest()});i+=1
  if root.find('s:IsTruncated',ns).text=='false':break
  token=root.find('s:NextContinuationToken',ns).text
 print(orbit,'keys',sum(x['n'] for x in pages if x['prefix']==prefix),flush=True)
# products 22 May to 31 May 2025; filename includes satellite observation date, not ingestion date
chosen=[k for k in keys if k.endswith('.json') and re.search(r'-2505(?:2[2-9]|3[01])_',k)]
print('selected',len(chosen),flush=True);domain=box(-94.1241,36.4828,-92.5184,37.8490)
def get(k):
 f=R/pathlib.PurePosixPath(k).name
 for i in range(3):
  try:
   if not f.exists():
    r=requests.get(base+k,timeout=40);r.raise_for_status();f.write_bytes(r.content)
   b=f.read_bytes();j=json.loads(b);g=shape(j['geometry']);assert j['type']=='Feature' and g.is_valid
   return {'key':k,'id':j['id'],'datetime':j['properties']['datetime'],'bbox':j['bbox'],'intersects_bbox':g.intersects(domain),'sha256':hashlib.sha256(b).hexdigest()}
  except Exception as e:
   if i==2:return {'key':k,'error':repr(e)}
   time.sleep(1+i)
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex: results=list(ex.map(get,chosen))
match=[x for x in results if x.get('intersects_bbox')];errors=[x for x in results if 'error'in x]
(O/'search_results.json').write_text(json.dumps({'bbox':list(domain.bounds),'window':['2025-05-22','2025-05-31'],'prefix_scope':['ALOS2593','ALOS2594','ALOS2595'],'listing_pages':pages,'selected_count':len(chosen),'errors':errors,'intersecting':match,'all_items':results},indent=2),encoding='utf8')
print('FINISH',len(results),'MATCH',len(match),'ERROR',len(errors),flush=True)
for x in match:print(x,flush=True)
