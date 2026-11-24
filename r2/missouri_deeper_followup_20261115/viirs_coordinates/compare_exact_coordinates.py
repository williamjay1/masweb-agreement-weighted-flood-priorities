import json,glob,h5py,rasterio,numpy as np,pyproj,hashlib
from pathlib import Path
out=Path(r'external/analysis/Geocarto_R2_20261115/missouri_neartime_viirs_followup_20261115/viirs_geolocation_new')
src=Path(r'external/data/Geocarto_R2_20261115/raw/missouri_noaa_viirs_20261115')
nc=next(src.glob('*s202505301737140*.nc')); tif=next(src.glob('*s202505301737140*.tif'))
with h5py.File(nc,'r') as ds:
 lon=ds['lon'][:].astype('float64');lat=ds['lat'][:].astype('float64'); info={'lon':{str(k):str(v) for k,v in ds['lon'].attrs.items()},'lat':{str(k):str(v) for k,v in ds['lat'].attrs.items()}}
with rasterio.open(tif) as d:
 trans=d.transform; shape=(d.height,d.width);tags=d.tags()
g=pyproj.Geod(ellps='WGS84')
points=[]
for row,col in [(0,0),(0,4447),(4447,0),(4447,4447),(2137,3447),(2211,3352),(2212,3352)]:
 ncx,ncy=float(lon[col]),float(lat[row]);tx,ty=trans*(col+.5,row+.5);az,az2,dist=g.inv(ncx,ncy,tx,ty)
 points.append({'row':row,'column':col,'netcdf_coordinate':[ncx,ncy],'tiff_cell_center':[tx,ty],'geodesic_difference_m':dist})
res={'nc':str(nc),'tiff':str(tif),'array_size':shape,'lat_lon_attributes':info,'geotiff_transform':list(trans),'geotiff_tags':tags,'points':points,'interpretation':'Distances are separations of two metadata-derived placements of identical array cells, not measured accuracy, standard error, uncertainty interval, or confirmed bound on actual error. The true position need not lie between these interpretations. TIFF center and NetCDF coordinates use the exact coordinate arrays.'}
(out/'coordinate_comparison.json').write_text(json.dumps(res,indent=2),encoding='utf8');print(json.dumps(res,indent=2))
