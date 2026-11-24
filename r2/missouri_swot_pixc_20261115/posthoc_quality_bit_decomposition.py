"""Post-hoc decomposition of the two PIXC quality flag bits.

Outputs exploratory diagnostics only. Never interpret absence of a point as dry.
Reads only exact manifest byte count and NASA MD5 verified inputs.
"""
from pathlib import Path
import hashlib,json
from collections import Counter,defaultdict
import h5py,numpy as np,pandas as pd
from pyproj import Transformer
B=Path('external/analysis/Geocarto_R2_20261115'); W=B/'missouri_neartime_viirs_followup_20261115'
R=Path('external/data/Geocarto_R2_20261115/raw/missouri_swot_pixc_20261115')
O=W/'swot_pixc_analysis/outputs'; O.mkdir(exist_ok=True)
M=pd.read_csv(W/'user_instructions_20261115/SWOT_PIXC_8_files_manifest.csv')
S=pd.read_csv(B/'missouri_swot_new_footprints_20261115/point_nominal_footprint_membership.csv')
lookup={(int(round((x-162015)/30)),int(round((1658115-y)/30))):i for i,(x,y) in enumerate(zip(S.x_epsg5070,S.y_epsg5070))}
assert len(lookup)==len(S)
tr=Transformer.from_crs(4326,5070,always_xy=True)
# flags code 1 = classification bit 4, 2 = geolocation bit 4.
cell_flags={p:defaultdict(set) for p in ('033_259','033_272')}; point_counts={p:Counter() for p in cell_flags}; audit=[]
for row in M.itertuples(index=False):
 p=R/row.filename
 if not p.is_file() or p.stat().st_size!=row.bytes: raise RuntimeError(f'Missing or wrong size: {row.filename}')
 h=hashlib.md5()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
 if h.hexdigest()!=row.md5_nasa.lower(): raise RuntimeError(f'MD5 mismatch: {row.filename}')
 orbit='_'.join(row.tile.split('_')[:2]); audit.append({'file':row.filename,'md5':h.hexdigest()})
 with h5py.File(p) as f:
  g=f['pixel_cloud']; n=len(g['latitude'])
  for i in range(0,n,300000):
   c=g['classification'][i:i+300000]; cq=g['classification_qual'][i:i+300000]; gq=g['geolocation_qual'][i:i+300000]
   m=np.isin(c,[3,4]) & ((cq & np.uint32(0xfffffffb))==0) & ((gq & np.uint32(0xfffffffb))==0)
   if not m.any():continue
   lon=g['longitude'][i:i+300000][m]; lat=g['latitude'][i:i+300000][m]
   x,y=tr.transform(lon,lat); x=np.asarray(x);y=np.asarray(y)
   ok=np.isfinite(x)&np.isfinite(y)&(np.abs(x)<1e7)&(np.abs(y)<1e7)
   cols=np.floor((x[ok]-162000)/30).astype(np.int64); rows=np.floor((1658130-y[ok])/30).astype(np.int64)
   a=cq[m][ok];b=gq[m][ok]
   for col,r,qq,gg in zip(cols,rows,a,b):
    index=lookup.get((int(col),int(r)))
    if index is None or not S.loc[index,'in_nominal_'+orbit]: continue
    code=int(qq==4)+2*int(gg==4)
    cell_flags[orbit][index].add(code);point_counts[orbit][code]+=1

combined=defaultdict(set)
for orbit in cell_flags:
 for i,flags in cell_flags[orbit].items(): combined[i].update(flags)
cell_flags['either']=combined;point_counts['either']=point_counts['033_259']+point_counts['033_272']
categories=[]; scenarios=[]
for orbit in ('033_259','033_272','either'):
 for code in range(4):
  idx=[i for i,flags in cell_flags[orbit].items() if code in flags]; sub=S.iloc[idx]
  categories.append({'scope':orbit,'classification_bit4':bool(code&1),'geolocation_bit4':bool(code&2),
    'matched_points':int(point_counts[orbit][code]),'distinct_cells_containing_this_combination':len(idx),
    'both_optical_water_cells':int(((sub.s30==1)&(sub.l30==1)).sum())})
 for scenario,allowed in [('strict',{0}),('classification_bit4_only',{0,1}),('geolocation_bit4_only',{0,2}),('both_bits_allowed',{0,1,2,3})]:
  idx=[i for i,flags in cell_flags[orbit].items() if flags & allowed];sub=S.iloc[idx]
  scenarios.append({'scope':orbit,'scenario':scenario,'unique_cells':len(idx),
    's30_water':int(sub.s30.sum()),'l30_water':int(sub.l30.sum()),'both_optical_water':int(((sub.s30==1)&(sub.l30==1)).sum())})
cell_records=[]
for orbit in ('033_259','033_272','either'):
 for i,flags in cell_flags[orbit].items():
  cell_records.append({'scope':orbit,'sample_id':i,'point_flag_combinations':','.join(map(str,sorted(flags))),
                       'has_classification_bit4':bool(any(c&1 for c in flags)),
                       'has_geolocation_bit4':bool(any(c&2 for c in flags)),
                       's30':int(S.loc[i,'s30']),'l30':int(S.loc[i,'l30'])})
pd.DataFrame(categories).to_csv(O/'posthoc_quality_bit_combinations.csv',index=False)
pd.DataFrame(scenarios).to_csv(O/'posthoc_quality_bit_scenarios.csv',index=False)
pd.DataFrame(cell_records).to_csv(O/'posthoc_quality_bit_cells.csv',index=False)
(O/'posthoc_quality_bit_provenance.json').write_text(json.dumps({'analysis':'post-hoc exploratory after observing first file; class 3/4; nested allowances; point categories may overlap at cell level',
 'flag_1':'classification bit 4 detected_water_but_no_prior_water',
 'flag_2':'geolocation bit 4 phase_unwrapping_suspect','files':audit,'categories':categories,'scenarios':scenarios},indent=2),encoding='utf-8')
print(json.dumps({'categories':categories,'scenarios':scenarios},indent=2))
