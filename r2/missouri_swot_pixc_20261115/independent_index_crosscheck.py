"""Independent pixel-to-raster-index check; fully synthetic tests elsewhere.
Only reads files whose byte counts and NASA MD5 match the manifest.
"""
import json,hashlib
from pathlib import Path
import h5py,numpy as np,pandas as pd
from pyproj import Transformer
base=Path('external/analysis/Geocarto_R2_20261115')
work=base/'missouri_neartime_viirs_followup_20261115'; out=work/'swot_pixc_analysis/outputs'
raw=Path('external/data/Geocarto_R2_20261115/raw/missouri_swot_pixc_20261115')
manifest=pd.read_csv(work/'user_instructions_20261115/SWOT_PIXC_8_files_manifest.csv')
sample=pd.read_csv(base/'missouri_swot_new_footprints_20261115/point_nominal_footprint_membership.csv')
# Transform from source optical raster, independently read and verified by verify_optical_sample.py.
sample_lookup={(int(round((x-162015)/30)),int(round((1658115-y)/30))):i for i,(x,y) in enumerate(zip(sample.x_epsg5070,sample.y_epsg5070))}
assert len(sample_lookup)==len(sample)
sets={orbit:{mode:set() for mode in ('strict','exploratory')} for orbit in ('033_259','033_272')}
transform=Transformer.from_crs(4326,5070,always_xy=True)
verified=[]
for row in manifest.itertuples(index=False):
 p=raw/row.filename
 if not p.exists() or p.stat().st_size!=row.bytes: continue
 h=hashlib.md5()
 with p.open('rb') as stream:
  for b in iter(lambda:stream.read(8*1024*1024),b''): h.update(b)
 if h.hexdigest()!=row.md5_nasa.lower(): continue
 orbit='_'.join(row.tile.split('_')[:2]); verified.append(row.filename)
 with h5py.File(p) as f:
  g=f['pixel_cloud']; n=len(g['latitude'])
  for i in range(0,n,300000):
   c=g['classification'][i:i+300000]; cq=g['classification_qual'][i:i+300000]; gq=g['geolocation_qual'][i:i+300000]
   m=np.isin(c,[3,4]) & ((cq & np.uint32(0xfffffffb))==0) & ((gq & np.uint32(0xfffffffb))==0)
   if not m.any():continue
   lon=g['longitude'][i:i+300000][m]; lat=g['latitude'][i:i+300000][m]
   x,y=transform.transform(lon,lat); x=np.asarray(x);y=np.asarray(y)
   good=np.isfinite(x)&np.isfinite(y)&(np.abs(x)<1e7)&(np.abs(y)<1e7)
   cols=np.floor((x[good]-162000)/30).astype(np.int64)
   rows=np.floor((1658130-y[good])/30).astype(np.int64)
   a=cq[m][good];b=gq[m][good]
   for col,r,qq,gg in zip(cols,rows,a,b):
    index=sample_lookup.get((int(col),int(r)))
    if index is None or not sample.loc[index,'in_nominal_'+orbit]: continue
    sets[orbit]['exploratory'].add(index)
    if qq==0 and gg==0: sets[orbit]['strict'].add(index)
records=[]
for orbit in ('033_259','033_272','either'):
 for mode in ('strict','exploratory'):
  idx=sets[orbit][mode] if orbit!='either' else sets['033_259'][mode] | sets['033_272'][mode]
  sub=sample.iloc[sorted(idx)]
  records.append(dict(orbit=orbit,scenario=mode,matched_unique=len(idx),s30_water=int(sub.s30.sum()),l30_water=int(sub.l30.sum()),both_water=int(((sub.s30==1)&(sub.l30==1)).sum())))
(out/'independent_index_crosscheck.json').write_text(json.dumps(dict(verified=verified,counts=records),indent=2),encoding='utf-8')
print(json.dumps(records,indent=2))
