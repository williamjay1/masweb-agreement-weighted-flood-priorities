import json, collections
from pathlib import Path
import h5py, numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
import analyze_swot_pixc as a

# This diagnostic is restricted to files independently verified against the NASA manifest.
sample=a.load_sample(a.OPTICAL,a.NOMINAL)
rows=pd.read_csv(a.MANIFEST).to_dict('records')
results=[]
for row in rows:
 p=a.RAW/row['filename']
 if not p.exists() or p.stat().st_size!=int(row['bytes']) or a.md5(p)!=row['md5_nasa'].lower(): continue
 orbit='_'.join(row['tile'].split('_')[:2]); sub=sample[sample['in_nominal_'+orbit]]
 xy=sub[['x','y']].to_numpy(); tree=cKDTree(xy); bounds=(xy.min(axis=0)-15,xy.max(axis=0)+15)
 trans=Transformer.from_crs(4326,5070,always_xy=True); hist=collections.Counter(); totals=collections.Counter()
 with h5py.File(p) as f:
  g=f['pixel_cloud']; length=len(g['latitude'])
  for i in range(0,length,250000):
   arrays={k:g[k][i:i+250000] for k in a.FIELDS}
   ok=np.ones(len(arrays['latitude']),bool)
   for k,v in arrays.items(): ok &= a.good_fill(v,g[k])
   cls=arrays['classification']; ok &= np.isin(cls,[3,4,5])
   if not ok.any(): continue
   lon=a.transformed(arrays['longitude'][ok],g['longitude']); lat=a.transformed(arrays['latitude'][ok],g['latitude'])
   xx,yy=trans.transform(lon,lat); xx=np.asarray(xx); yy=np.asarray(yy)
   inbound=np.isfinite(xx)&np.isfinite(yy)&(xx>=bounds[0][0])&(xx<=bounds[1][0])&(yy>=bounds[0][1])&(yy<=bounds[1][1])
   if not inbound.any(): continue
   valid_arrays={k:v[ok][inbound] for k,v in arrays.items()}
   points=np.column_stack([xx[inbound],yy[inbound]])
   dist,ix=tree.query(points,k=1,p=np.inf,distance_upper_bound=15.0,workers=1)
   matched=np.isfinite(dist)
   for c,cq,gq in zip(valid_arrays['classification'][matched],valid_arrays['classification_qual'][matched],valid_arrays['geolocation_qual'][matched]):
    hist[(int(c),int(cq),int(gq))]+=1
   totals['bbox_points']+=len(points); totals['matched_points']+=int(matched.sum())
 results.append({'filename':p.name,'orbit':orbit,'counts':dict(totals),'matched_flag_combinations':[{'class':c,'classification_qual':cq,'geolocation_qual':gq,'count':n} for (c,cq,gq),n in hist.most_common()]})
out=Path(__file__).parent/'outputs'/'quality_flag_diagnostic.json';out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
