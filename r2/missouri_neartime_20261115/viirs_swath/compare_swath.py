import glob,json,h5py,numpy as np,rasterio
from rasterio.transform import rowcol
from pathlib import Path
base=Path('external/analysis/Geocarto_R2_20261115/missouri_viirs_swath_check_20261115')
f='external/data/Geocarto_R2_20261115/raw/missouri_viirs_swath_20261115/'
original=Path('external/data/Geocarto_R2_20261115/raw/missouri_noaa_viirs_20261115')
tif=next(original.glob('*s202505301737140*.tif'));nc=next(original.glob('*.nc'))
with rasterio.open(tif) as d: cat=d.read(1);gt=d.transform
with rasterio.open(nc) as d:
 with rasterio.open(d.subdatasets[0]) as sub: gn=sub.transform
with h5py.File(glob.glob(f+'GITCO*.h5')[0],'r') as h:
 a=h['All_Data/VIIRS-IMG-GEO-TC_All']; lat=a['Latitude'][:];lon=a['Longitude'][:]
with h5py.File(glob.glob(f+'SVI02*.h5')[0],'r') as h:
 a=h['All_Data/VIIRS-I2-SDR_All'];raw=a['Reflectance'][:];q=a['QF1_VIIRSIBANDSDR'][:];factors=a['ReflectanceFactors'][:]
# QF == 0 requires all quality bits good, none saturated/missing/out of range.
m=(lon>=-94.1241)&(lon<=-92.5184)&(lat>=36.4828)&(lat<=37.8490)&(q==0)&(raw<65528)
x=lon[m].astype('float64');y=lat[m].astype('float64');v=raw[m].astype('float32')*factors[0]+factors[1]
def sample(g):
 c=np.floor((x-g.c)/g.a).astype(int);r=np.floor((y-g.f)/g.e).astype(int)
 return cat[r,c]
a=sample(gn);b=sample(gt)
def stat(mask):
 z=v[mask]
 return {'count':int(z.size),'mean_i2':float(np.mean(z)) if z.size else None,'median_i2':float(np.median(z)) if z.size else None,'p10_i2':float(np.quantile(z,.1)) if z.size else None,'p90_i2':float(np.quantile(z,.9)) if z.size else None}
out={'input_qa':'QF1_VIIRSIBANDSDR == 0; raw reflectance < 65528; bounding box only. No same-pass cloud mask available.','source_pixels':int(m.sum()),'netcdf_99':stat(a==99),'geotiff_99':stat(b==99),'netcdf_17':stat(a==17),'geotiff_17':stat(b==17),'paired_netcdf_99_tif_17':stat((a==99)&(b==17)),'paired_tif_99_netcdf_17':stat((b==99)&(a==17)),'shared_99':stat((a==99)&(b==99)),'disagree_any':int(np.count_nonzero(a!=b)),'transforms':{'netcdf':list(gn),'geotiff':list(gt)},'caveat':'Exploratory diagnostic after discrepancy was known, correlated swath samples, no cloud mask, daily composite can use other VIIRS overpasses; no flood accuracy, no decisive geolocation determination.'}
(base/'swath_grid_diagnostic.json').write_text(json.dumps(out,indent=2),encoding='utf8'); print(json.dumps(out,indent=2))
