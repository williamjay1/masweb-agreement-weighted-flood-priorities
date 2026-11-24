import pathlib,requests,hashlib,json,concurrent.futures
r=pathlib.Path('external/data/Geocarto_R2_20261115/raw/missouri_alos2_aws_followup_20261115');out=pathlib.Path('external/analysis/Geocarto_R2_20261115/missouri_flood_reference_followup_20261115/alos2_aws');st='ALOS2594110700-250524_WBDR2.2GUA';base='https://jaxaalos2.s3.us-west-2.amazonaws.com/palsar2/L2.2/2025/'
files=[st+'_HH_SLP.tif',st+'_HV_SLP.tif',st+'_MSK.tif',st+'_summary.xml']
def task(name):
 f=r/name;t=r/(name+'.part')
 if not f.exists():
  with requests.get(base+name,stream=True,timeout=(30,90)) as resp:
   resp.raise_for_status();length=int(resp.headers.get('content-length','0'))
   with t.open('xb') as w:
    for b in resp.iter_content(1024*1024):w.write(b)
   assert not length or t.stat().st_size==length
  t.rename(f)
 with f.open('rb') as h:sha=hashlib.file_digest(h,'sha256').hexdigest()
 print(name, f.stat().st_size,sha,flush=True)
 return {'name':name,'bytes':f.stat().st_size,'sha256':sha,'url':base+name}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:items=list(e.map(task,files))
(out/'asset_downloads.json').write_text(json.dumps(items,indent=2),encoding='utf8')
