from pathlib import Path
import pandas as pd, numpy as np, rasterio, json, datetime
from shapely.geometry import shape, Point
from shapely.prepared import prep
from pyproj import Transformer
from rasterio.sample import sample_gen
p=Path(r'external/analysis/Geocarto_R2_20261115/missouri_geo_independent_audit_20261115'); p.mkdir(exist_ok=True)
r=Path(r'external/data/Geocarto_R2_20261115/raw/missouri_alos2_aws_followup_20261115');s=Path(r'external/analysis/Geocarto_R2_20261115/missouri_flood_reference_followup_20261115/alos2_aws')
orig=pd.read_csv(r'external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv');agent=pd.read_csv(s/'alos2_point_samples_with_polygon.csv'); assert len(orig)==len(agent)==5661
files={k:next(r.glob('*250524*'+k+'.tif')) for k in ['HH_SLP','HV_SLP','MSK']};ds={k:rasterio.open(v) for k,v in files.items()};reference=ds['HH_SLP']; px,py=Transformer.from_crs(5070,32615,always_xy=True).transform(orig.x.to_numpy(),orig.y.to_numpy()); pix=[reference.index(x,y) for x,y in zip(px,py)];rc=np.array(pix);inside=(rc[:,0]>=0)&(rc[:,0]<reference.height)&(rc[:,1]>=0)&(rc[:,1]<reference.width)
assert (rc[:,0]==agent.sar_row.to_numpy()).all() and (rc[:,1]==agent.sar_col.to_numpy()).all()
ind=np.flatnonzero(inside); coords=[(px[j],py[j]) for j in ind];data={}
for name,f in ds.items():
 v=np.full(len(orig),np.nan);v[ind]=[z[0] for z in sample_gen(f,coords)];data[name]=v
 for k in ['hh' if name=='HH_SLP' else 'hv' if name=='HV_SLP' else 'mask']:
  assert np.array_equal(np.isnan(v),np.isnan(agent[k]))
  assert np.array_equal(v[ind],agent.loc[ind,k].values)
for f in ds.values():f.close()
valid=inside & (data['MSK']==1) & (data['HH_SLP']>0) & (data['HV_SLP']>0)
assert np.array_equal(valid,agent.valid.to_numpy());stac=json.loads((r/'ALOS2594110700-250524_WBDR2.2GUA.json').read_text()); poly=prep(shape(stac['geometry'])); lon,lat=Transformer.from_crs(5070,4326,always_xy=True).transform(orig.x.to_numpy(),orig.y.to_numpy()); geom=np.array([poly.covers(Point(x,y)) for x,y in zip(lon,lat)]);assert np.array_equal(geom,agent.stac_polygon.to_numpy())
report={'stac_time':stac['properties']['datetime'],'image_rectangle_count':int(inside.sum()),'stac_geometry_count':int(geom.sum()),'mask_one_valid_count':int(valid.sum()),'mask_one_outside_stac':int((valid&~geom).sum()),'stac_inside_but_no_valid':int((geom&~valid).sum()),'unique_valid_sar_cells':int(len(set(zip(rc[valid,0],rc[valid,1])))), 'mask_counts':{str(int(z)):int(((data['MSK']==z)&inside).sum()) for z in np.unique(data['MSK'][inside])},'groups':{}}
for a in (0,1):
 for b in (0,1):
  m=valid & (orig.s30==a) & (orig.l30==b);g={'n':int(m.sum())}
  for k in ('HH_SLP','HV_SLP'):
   v=20*np.log10(data[k][m])-83;g[k+'_quartiles']=[float(vv) for vv in np.quantile(v,[.25,.5,.75])]
  report['groups'][f'S{a}L{b}']=g
print(json.dumps(report,indent=2));(p/'alos2_audit_independent.json').write_text(json.dumps(report,indent=2),encoding='utf8')
