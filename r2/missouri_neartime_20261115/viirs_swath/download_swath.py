import requests,hashlib,json,os
base='https://noaa-nesdis-n20-pds.s3.amazonaws.com/'
keys=['VIIRS-IMG-GEO-TC/2025/05/30/GITCO_j01_d20250530_t2005104_e2006349_b39023_c20250530202821970000_oeac_ops.h5','VIIRS-I2-SDR/2025/05/30/SVI02_j01_d20250530_t2005104_e2006349_b39023_c20250530203108339000_oeac_ops.h5']
out='external/data/Geocarto_R2_20261115/raw/missouri_viirs_swath_20261115';meta=[]
for k in keys:
 url=base+k;p=out+'/'+os.path.basename(k)
 if os.path.exists(p):raise FileExistsError(p)
 h=hashlib.sha256();n=0
 with requests.get(url,stream=True,timeout=60) as r:
  r.raise_for_status()
  with open(p,'xb') as f:
   for chunk in r.iter_content(1024*1024):f.write(chunk);h.update(chunk);n+=len(chunk)
  exp=int(r.headers['Content-Length'])
 if n!=exp:raise ValueError((n,exp))
 meta.append({'url':url,'path':p,'bytes':n,'sha256':h.hexdigest()});print(meta[-1],flush=True)
with open('external/analysis/Geocarto_R2_20261115/missouri_viirs_swath_check_20261115/source_manifest.json','w') as f:json.dump(meta,f,indent=2)
