import requests,io,h5py,json,concurrent.futures,re
from xml.etree import ElementTree as E
base='https://noaa-nesdis-n20-pds.s3.amazonaws.com/'
ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
keys=[]
for hr in ['17','18','19','20','21']:
 p='VIIRS-IMG-GEO-TC/2025/05/30/GITCO_j01_d20250530_t'+hr
 r=requests.get(base,params={'list-type':'2','prefix':p},timeout=25);r.raise_for_status()
 keys += [x.text for x in E.fromstring(r.content).findall('.//s:Key',ns)]
# first granule in each five minute bin
selected={}
for k in keys:
 t=re.search(r'_t(\d{6})\d_',k).group(1);slot=t[:2]+str(int(t[2:4])//5).zfill(2)
 selected.setdefault(slot,k)
class RF(io.RawIOBase):
 def __init__(self,url): self.url=url;self.pos=0;self.size=int(requests.head(url,timeout=20).headers['Content-Length']);self.session=requests.Session();self.cache={}
 def readable(self):return True
 def seekable(self):return True
 def tell(self):return self.pos
 def seek(self,p,w=0):self.pos=p if w==0 else self.pos+p if w==1 else self.size+p;return self.pos
 def readinto(self,b):
  p=self.pos;n=min(len(b),self.size-p)
  if n<=0:return 0
  st=(p//262144)*262144;en=min(max(st+262144,p+n),self.size)-1;key=(st,en)
  if key not in self.cache:
   r=self.session.get(self.url,headers={'Range':f'bytes={st}-{en}'},timeout=35);r.raise_for_status();self.cache[key]=r.content
  z=self.cache[key][p-st:p-st+n];b[:len(z)]=z;self.pos+=len(z);return len(z)
def run(k):
 try:
  f=RF(base+k)
  with h5py.File(f,'r') as h:
   a=h['Data_Products/VIIRS-IMG-GEO-TC/VIIRS-IMG-GEO-TC_Gran_0'].attrs
   vals={x:float(a[x].ravel()[0]) for x in ['North_Bounding_Coordinate','South_Bounding_Coordinate','East_Bounding_Coordinate','West_Bounding_Coordinate']}
  return dict(key=k,**vals)
 except Exception as e:return dict(key=k,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 results=list(pool.map(run,selected.values()))
out='external/analysis/Geocarto_R2_20261115/missouri_viirs_swath_check_20261115/swath_geo_metadata.json'
with open(out,'w') as f:json.dump(results,f,indent=2)
for x in results:
 if x.get('South_Bounding_Coordinate',90)<=38 and x.get('North_Bounding_Coordinate',-90)>=37 and x.get('West_Bounding_Coordinate',180)<=-93 and x.get('East_Bounding_Coordinate',-180)>=-94:print(x,flush=True)
print('n',len(results),'errors',sum('error'in x for x in results),flush=True)
