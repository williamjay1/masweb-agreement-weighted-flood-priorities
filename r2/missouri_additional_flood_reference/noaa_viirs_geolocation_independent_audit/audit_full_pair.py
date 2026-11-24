from pathlib import Path
import numpy as np,rasterio,json
from rasterio.windows import Window,from_bounds
from rasterio.warp import reproject,Resampling
from scipy.ndimage import label
p=Path(r'external/analysis/Geocarto_R2_20261115/missouri_geo_independent_audit_20261115'); q=Path(r'external/analysis/Geocarto_R2_20261115/missouri_viirs_geo_followup_20261115'); src=Path(r'external/data/Geocarto_R2_20261115/raw/missouri_viirs_geolocation_20261115/occurrence_100W_40N_v1_5_2024.tif');old=Path(r'external/data/Geocarto_R2_20261115/raw/missouri_noaa_viirs_20261115')
with rasterio.open(next(old.glob('*.nc'))) as con:
 with rasterio.open(con.subdatasets[0]) as d: nt=d.transform
with rasterio.open(next(old.glob('*s202505301737140*.tif'))) as d:
 tt=d.transform; win=Window(3227,2122,472,401); data=d.read(1,window=win)
with rasterio.open(src) as s:
 bounds=(-94.1241,36.4828,-92.5184,37.8490); w=from_bounds(bounds[0]-.01,bounds[1]-.01,bounds[2]+.01,bounds[3]+.01,transform=s.transform).round_offsets().round_lengths();raw=s.read(1,window=w); st=s.window_transform(w)
 valid=(raw!=255).astype('uint8');result={'raw_source':{'shape':raw.shape,'total':int(raw.size),'nodata':int((raw==255).sum()),'nodata_proportion':float((raw==255).mean())},'classes':{}}
 for code in [99,17]:
  mask=data==code; n=np.load(q/'jrc95_mean_netcdf.npy');t=np.load(q/'jrc95_mean_geotiff.npy');delta=t[mask]-n[mask];eps=1e-7
  im, count=label(mask,structure=np.ones((3,3)));sizes=np.bincount(im[mask]);sizes[0]=0;largest=np.sort(sizes)[::-1][:10]
  result['classes'][str(code)]={'count':int(mask.sum()),'geotiff_minus_netcdf_mean':float(delta.mean()),'median':float(np.median(delta)),'positive':int((delta>eps).sum()),'negative':int((delta< -eps).sum()),'near_equal_1e_7':int((np.abs(delta)<=eps).sum()),'components_8_connected':int(count),'largest_10_components_cells':largest.tolist()}
 for name,transform in [('netcdf',nt),('geotiff',tt)]:
  dst=np.empty(data.shape,dtype='float32');reproject(source=valid,destination=dst,src_transform=st,src_crs=s.crs,dst_transform=rasterio.windows.transform(win,transform),dst_crs='EPSG:4326',resampling=Resampling.average,num_threads=4)
  for code in [99,17]:
   vals=dst[data==code];result['classes'][str(code)][name+'_partially_nodata_count']=int((vals<1-1e-7).sum());result['classes'][str(code)][name+'_max_nodata_fraction']=float(np.max(1-vals))
(p/'full_nodata_pair_and_spatial_audit.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
