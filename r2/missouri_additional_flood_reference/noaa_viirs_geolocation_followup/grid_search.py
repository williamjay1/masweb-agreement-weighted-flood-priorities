from pathlib import Path
import glob,json,numpy as np,rasterio
from rasterio.windows import from_bounds,Window
from rasterio.warp import reproject,Resampling
from rasterio.transform import Affine
b=Path('external/analysis/Geocarto_R2_20261115/missouri_viirs_geo_followup_20261115')
raw=Path('external/data/Geocarto_R2_20261115/raw/missouri_viirs_geolocation_20261115/occurrence_100W_40N_v1_5_2024.tif')
tif=next(Path('external/data/Geocarto_R2_20261115/raw/missouri_noaa_viirs_20261115').glob('*s202505301737140*.tif'))
minx,miny,maxx,maxy=-94.1241,36.4828,-92.5184,37.8490
with rasterio.open(tif) as t:
 win=from_bounds(minx,miny,maxx,maxy,transform=t.transform).round_offsets().round_lengths();win=Window(win.col_off+2,win.row_off+2,win.width-4,win.height-4)
 water=t.read(1,window=win);orig=t.transform*Affine.translation(win.col_off,win.row_off)
with rasterio.open(raw) as f:
 w=from_bounds(minx-.01,miny-.01,maxx+.01,maxy+.01,transform=f.transform).round_offsets().round_lengths();occ=f.read(1,window=w);source=np.where(occ==255,255,(occ>=95).astype('uint8')).astype('uint8')
 results=[]
 for y in [-.5,0,.5]:
  for x in [-.5,0,.5]:
   dst=np.full(water.shape,np.nan,dtype='float32');target=orig*Affine.translation(x,y)
   reproject(source=source,destination=dst,src_transform=f.window_transform(w),src_crs=f.crs,src_nodata=255,dst_transform=target,dst_crs='EPSG:4326',dst_nodata=np.nan,resampling=Resampling.average,num_threads=4)
   wet=dst[(water==99)&np.isfinite(dst)];veg=dst[(water==17)&np.isfinite(dst)]
   results.append({'col_shift_pixels_east':x,'row_shift_pixels_south':y,'normal_water_n':int(wet.size),'normal_water_mean':float(wet.mean()),'vegetation_n':int(veg.size),'vegetation_mean':float(veg.mean())})
   print(results[-1],flush=True)
(b/'alignment_grid_search.json').write_text(json.dumps(results,indent=2),encoding='utf8')
