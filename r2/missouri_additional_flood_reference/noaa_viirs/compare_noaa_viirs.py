from pathlib import Path
import glob, hashlib, json
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.transform import rowcol

RAW=Path('external/data/Geocarto_R2_20261115/raw/missouri_noaa_viirs_20261115')
OUT=Path('external/analysis/Geocarto_R2_20261115/missouri_flood_reference_20261115/flood_maps')
SOURCE=Path('external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv')
BASE='https://noaa-jpss.s3.amazonaws.com/JPSS_Blended_Products/VFM_1day_GLB/'
df=pd.read_csv(SOURCE)
assert len(df)==5661 and df[['x','y']].duplicated().sum()==0
assert set(df.s30.unique()).issubset({0,1}) and set(df.l30.unique()).issubset({0,1})
lon,lat=Transformer.from_crs('EPSG:5070','EPSG:4326',always_xy=True).transform(df.x.to_numpy(),df.y.to_numpy())
meta={'input_file':str(SOURCE),'input_sha256':hashlib.file_digest(SOURCE.open('rb'),'sha256').hexdigest(),'input_points':len(df),'longitude_minmax':[float(min(lon)),float(max(lon))], 'latitude_minmax':[float(min(lat)),float(max(lat))],'sources':[]}
nc=next(RAW.glob('*20250530*.nc'))
with rasterio.open(nc) as con: sub=con.subdatasets
with rasterio.open(sub[0]) as wd, rasterio.open(sub[1]) as qd:
 assert wd.transform==qd.transform and wd.shape==qd.shape
 rr,cc=rowcol(wd.transform,lon,lat);rr=np.array(rr);cc=np.array(cc)
 assert all((rr>=0)&(rr<wd.height)&(cc>=0)&(cc<wd.width))
 wa=wd.read(1); qa=qd.read(1)
 z=df[['x','y','s30','l30']].copy();z['longitude']=lon;z['latitude']=lat;z['source_row']=rr;z['source_col']=cc;z['water_code']=wa[rr,cc];z['quality_flag']=qa[rr,cc]
 z['flood_class']=(z.water_code==15)|z.water_code.between(101,200)
 z.to_csv(OUT/'netcdf_may30_5661_centres.csv',index=False)
 cells=z.groupby(['source_row','source_col','water_code','quality_flag'],as_index=False).agg(n_centres=('s30','size'),s30_water_centres=('s30','sum'),l30_water_centres=('l30','sum'),longitude_min=('longitude','min'),longitude_max=('longitude','max'),latitude_min=('latitude','min'),latitude_max=('latitude','max'))
 cells['s30_any']=cells.s30_water_centres.gt(0);cells['l30_any']=cells.l30_water_centres.gt(0)
 cells['flood_class']=(cells.water_code==15)|cells.water_code.between(101,200)
 cells.to_csv(OUT/'netcdf_may30_unique_cells.csv',index=False)
 cells[cells.flood_class].to_csv(OUT/'netcdf_may30_flood_cells.csv',index=False)
 z.groupby(['water_code','quality_flag']).agg(centres=('s30','size'),s30_water_centres=('s30','sum'),l30_water_centres=('l30','sum')).to_csv(OUT/'netcdf_may30_centre_by_class_qa.csv')
 cells.groupby(['water_code','quality_flag']).agg(unique_cells=('n_centres','size'),s30_any_cells=('s30_any','sum'),l30_any_cells=('l30_any','sum'),centres=('n_centres','sum'),s30_water_centres=('s30_water_centres','sum'),l30_water_centres=('l30_water_centres','sum')).to_csv(OUT/'netcdf_may30_cell_by_class_qa.csv')
 meta['netcdf']={'filename':nc.name,'bytes':nc.stat().st_size,'sha256':hashlib.file_digest(nc.open('rb'),'sha256').hexdigest(),'url':BASE+'NetCDF/2025/05/30/'+nc.name,'water_transform':list(wd.transform),'water_crs':str(wd.crs),'water_tags':wd.tags(),'quality_tags':qd.tags(),'total_unique_cells':len(cells),'flood_cells':int(cells.flood_class.sum())}
 print('NETCDF centre\n',z.groupby(['water_code','quality_flag']).size().to_string()); print('NETCDF cells\n',cells.groupby(['water_code','quality_flag']).size().to_string());print('flood cells\n',cells[cells.flood_class].to_string(index=False))
for t in sorted(RAW.glob('*.tif')):
 with rasterio.open(t) as ds:
  r,c=rowcol(ds.transform,lon,lat);r=np.array(r);c=np.array(c);a=ds.read(1)
  tz=df[['x','y','s30','l30']].copy();tz['row']=r;tz['col']=c;tz['water_code']=a[r,c]
  tc=tz.groupby(['row','col','water_code'],as_index=False).agg(n_centres=('s30','size'),s30_water=('s30','sum'),l30_water=('l30','sum'))
  date=ds.tags()['NC_GLOBAL#Observingdate']
  tc.to_csv(OUT/f'tif_{date}_unique_cells.csv',index=False)
  print(date,'cells',len(tc), 'codes',tc.groupby('water_code').size().to_dict())
  entry={'file':t.name,'bytes':t.stat().st_size,'sha256':hashlib.file_digest(t.open('rb'),'sha256').hexdigest(),'url':BASE+f'TIF/{date[:4]}/{date[4:6]}/{date[6:]}/'+t.name,'transform':list(ds.transform),'time_coverage_start':ds.tags().get('NC_GLOBAL#time_coverage_start'),'time_coverage_end':ds.tags().get('NC_GLOBAL#time_coverage_end'),'classes':{str(k):int(v) for k,v in tc.groupby('water_code').size().to_dict().items()}}
  if date=='20250530':
   entry['same_array_index_unequal_count']=int(np.count_nonzero(a!=wa));entry['same_array_index_total']=int(a.size)
  meta['sources'].append(entry)
(OUT/'noaa_source_metadata_and_hashes.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf-8')
