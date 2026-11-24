from pathlib import Path
import glob,json,hashlib
import numpy as np,rasterio
from rasterio.windows import from_bounds,Window
from rasterio.warp import reproject,Resampling
from rasterio.transform import Affine
base=Path('external/analysis/Geocarto_R2_20261115/missouri_viirs_geo_followup_20261115')
raw=Path('external/data/Geocarto_R2_20261115/raw/missouri_viirs_geolocation_20261115/occurrence_100W_40N_v1_5_2024.tif')
old=Path('external/data/Geocarto_R2_20261115/raw/missouri_noaa_viirs_20261115')
nc=next(old.glob('*.nc'));tif=next(old.glob('*s202505301737140*.tif'))
# Original event rectangle. This analysis was devised after identifying the grid discrepancy.
minx,miny,maxx,maxy=-94.1241,36.4828,-92.5184,37.8490
with rasterio.open(tif) as t, rasterio.open(nc) as n:
 sub=n.subdatasets
 with rasterio.open(sub[0]) as nd:
  na=nd.transform; ta=t.transform
  win=from_bounds(minx,miny,maxx,maxy,transform=ta).round_offsets().round_lengths()
  # inset 2 whole pixels to remove edge differences
  win=Window(win.col_off+2,win.row_off+2,win.width-4,win.height-4)
  water=t.read(1,window=win)
  common={'shape':list(water.shape),'window':[win.row_off,win.col_off,win.height,win.width], 'water_count':int((water==99).sum()),'veg_count':int((water==17).sum())}
  transforms={'netcdf':na*Affine.translation(win.col_off,win.row_off),'geotiff':ta*Affine.translation(win.col_off,win.row_off)}
with rasterio.open(raw) as f:
 w=from_bounds(minx-.01,miny-.01,maxx+.01,maxy+.01,transform=f.transform).round_offsets().round_lengths()
 occurrence=f.read(1,window=w); st=f.window_transform(w)
 # 255 is nodata, 0 is no detected water, 95-100 is frequently observed water
 source=np.where(occurrence==255,255,(occurrence>=95).astype('uint8')).astype('uint8')
 results=[]
 for name,transform in transforms.items():
  dst=np.full(water.shape,np.nan,dtype='float32')
  reproject(source=source,destination=dst,src_transform=st,src_crs=f.crs,src_nodata=255,dst_transform=transform,dst_crs='EPSG:4326',dst_nodata=np.nan,resampling=Resampling.average,num_threads=4)
  for code in [99,17]:
   x=dst[(water==code)&np.isfinite(dst)]
   results.append({'grid':name,'class':code,'count':len(x),'mean_fraction_high_occurrence':float(x.mean()),'median':float(np.median(x)), 'positive_fraction_count':int((x>0).sum()), 'atleast_10pct_count':int((x>=.1).sum()),'atleast_50pct_count':int((x>=.5).sum())})
  np.save(base/f'jrc95_mean_{name}.npy',dst)
print(json.dumps({'common':common,'results':results},indent=2))
(base/'permanent_water_alignment.json').write_text(json.dumps({'common':common,'results':results,'source':str(raw),'note':'Retrospective contextual geolocation diagnostic against Landsat occurrence 1984–2024; not flood validation; common historical water influences class99, and dates/resolutions differ.'},indent=2),encoding='utf8')
