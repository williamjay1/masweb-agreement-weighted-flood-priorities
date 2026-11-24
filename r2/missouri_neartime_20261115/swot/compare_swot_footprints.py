import json
from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import unary_union

out=Path('external/analysis/Geocarto_R2_20261115/missouri_swot_new_footprints_20261115')
features=json.loads((out/'swot_nominal_footprints.geojson').read_text())['features']
groups={}
for ft in features:
 name=ft['properties']['granule']; k='_'.join(name.split('_')[4:6]); groups.setdefault(k,[]).append(shape(ft['geometry']))
groups={k:unary_union(v) for k,v in groups.items()}
df=pd.read_csv('external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv')
t=Transformer.from_crs(5070,4326,always_xy=True); lon,lat=t.transform(df.x.to_numpy(),df.y.to_numpy()); pts=[Point(x,y) for x,y in zip(lon,lat)]
a=np.array([groups['033_259'].covers(p) for p in pts]); b=np.array([groups['033_272'].covers(p) for p in pts]); s=df.s30==1; l=df.l30==1
rows=[]
for name,mask in [('all_optical_points',a|~a),('033_259',a),('033_272',b),('either_pass',a|b),('both_passes',a&b),('first_only',a&~b),('second_only',b&~a)]:
 rows.append({'domain':name,'points':int(mask.sum()),'s30_water':int((mask&s).sum()),'l30_water':int((mask&l).sum()),'both_water':int((mask&s&l).sum()),'either_water':int((mask&(s|l)).sum()),'both_dry':int((mask&~s&~l).sum())})
pd.DataFrame(rows).to_csv(out/'pass_nominal_optical_counts.csv',index=False)
pd.DataFrame({'x_epsg5070':df.x,'y_epsg5070':df.y,'s30':df.s30,'l30':df.l30,'in_nominal_033_259':a,'in_nominal_033_272':b}).to_csv(out/'point_nominal_footprint_membership.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))
