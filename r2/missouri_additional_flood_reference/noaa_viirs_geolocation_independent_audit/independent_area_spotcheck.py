from pathlib import Path
import json, numpy as np, rasterio
from rasterio.windows import Window, from_bounds
from pyproj import Geod
from rasterio.transform import xy
out=Path(r'external/analysis/Geocarto_R2_20261115/missouri_geo_independent_audit_20261115');out.mkdir(parents=True,exist_ok=True)
old=Path(r'external/data/Geocarto_R2_20261115/raw/missouri_noaa_viirs_20261115');nc=next(old.glob('*.nc'));tiff=next(old.glob('*s202505301737140*.tif'))
jrc=Path(r'external/data/Geocarto_R2_20261115/raw/missouri_viirs_geolocation_20261115/occurrence_100W_40N_v1_5_2024.tif')
bounds=(-94.1241,36.4828,-92.5184,37.8490)
with rasterio.open(nc) as n:
 with rasterio.open(n.subdatasets[0]) as ds:
  nt=ds.transform
with rasterio.open(tiff) as ds:
 tt=ds.transform
 win0=from_bounds(*bounds,transform=tt).round_offsets().round_lengths()
 win=Window(win0.col_off+2,win0.row_off+2,win0.width-4,win0.height-4)
 c=ds.read(1,window=win); nt2=rasterio.windows.transform(win,nt);tt2=rasterio.windows.transform(win,tt)
with rasterio.open(jrc) as ds:
 w=from_bounds(bounds[0]-.01,bounds[1]-.01,bounds[2]+.01,bounds[3]+.01,transform=ds.transform).round_offsets().round_lengths()
 a=ds.read(1,window=w); st=ds.window_transform(w)
 # exact Cartesian area over independent raw JRC cells, excluding documented no-data.
 def area_mean(transform,row,col):
  left,top=transform*(col,row);right,bottom=transform*(col+1,row+1)
  cs=max(0,int(np.floor((left-st.c)/st.a)));ce=min(a.shape[1],int(np.ceil((right-st.c)/st.a)))
  rs=max(0,int(np.floor((top-st.f)/st.e)));re=min(a.shape[0],int(np.ceil((bottom-st.f)/st.e)))
  xleft=st.c+np.arange(cs,ce)*st.a;xright=xleft+st.a
  ytop=st.f+np.arange(rs,re)*st.e;ybottom=ytop+st.e
  xweight=np.maximum(0,np.minimum(xright,right)-np.maximum(xleft,left))
  yweight=np.maximum(0,np.minimum(ytop,top)-np.maximum(ybottom,bottom))
  mat=a[rs:re,cs:ce];wt=np.outer(yweight,xweight);valid=mat!=255
  return np.sum(wt*valid*(mat>=95))/np.sum(wt*valid),float(np.sum(wt*(~valid))/np.sum(wt))
 rng=np.random.default_rng(2601);points=[]
 for code,npts in [(99,200),(17,100)]:
  inds=np.flatnonzero(c==code); chosen=rng.choice(inds,size=npts,replace=False)
  for flat in chosen:
   row,col=np.unravel_index(flat,c.shape)
   for name,transform in [('netcdf',nt2),('geotiff',tt2)]:
    q,nodata=area_mean(transform,int(row),int(col)); pts=np.load(Path(r'external/analysis/Geocarto_R2_20261115/missouri_viirs_geo_followup_20261115')/f'jrc95_mean_{name}.npy',mmap_mode='r');g=float(pts[row,col]);points.append({'class':code,'row':int(row),'col':int(col),'grid':name,'exact':float(q),'gdal':g,'absolute_difference':abs(g-q),'fraction_no_data':nodata})
res={'seed':2601,'n':len(points),'max_absolute_difference':max(p['absolute_difference'] for p in points),'mean_absolute_difference':float(np.mean([p['absolute_difference'] for p in points])),'max_nodata_fraction':max(p['fraction_no_data'] for p in points),'sample':points,'grid':{'shape':list(c.shape),'water':int((c==99).sum()),'vegetation':int((c==17).sum())}}
(out/'independent_area_spotcheck.json').write_text(json.dumps(res,indent=2),encoding='utf8')
print({k:v for k,v in res.items() if k!='sample'})
for name,transform in [('NetCDF',nt),('GeoTIFF',tt)]:
 print(name,'transform components',list(transform))
print('cell 2137,3447 geodesic center distance',Geod(ellps='WGS84').inv(*xy(nt,2137,3447,offset='center'),*xy(tt,2137,3447,offset='center'))[2])
