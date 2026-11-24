from pathlib import Path
import argparse,hashlib,json
import h5py,numpy as np,pandas as pd,rasterio
from rasterio.transform import from_origin,rowcol
from pyproj import Geod,Transformer

parser = argparse.ArgumentParser(description="Compare the two NOAA VIIRS grids and the producer's indexed coordinates.")
parser.add_argument('--netcdf', required=True, type=Path)
parser.add_argument('--geotiff', required=True, type=Path)
parser.add_argument('--output-dir', required=True, type=Path)
args = parser.parse_args()
nc, tif, OUT = args.netcdf, args.geotiff, args.output_dir
OUT.mkdir(parents=True, exist_ok=True)
supplement = Path(__file__).resolve().parents[1]
SAMPLES = supplement/'new_review_analyses/sar_followup/missouri_followup/rtc_may26_point_samples.csv'
with h5py.File(nc,'r') as ds:
    lon=ds['lon'][:].astype('float64');lat=ds['lat'][:].astype('float64')
    wat=ds['WaterDetection'][:]; quality=ds['QualityFlag'][:];attrs=ds['WaterDetection'].attrs
    att={k:float(np.asarray(attrs[k]).ravel()[0]) for k in ['ProjectionMinLongitude','ProjectionMaxLongitude','ProjectionMinLatitude','ProjectionMaxLatitude','ProjectionResolution']}
    print('attr',att,'coords endpoints',lon[0],lon[-1],lat[0],lat[-1]);print('size',wat.shape)
with rasterio.open(nc) as d: subs=d.subdatasets
with rasterio.open(subs[0]) as d: gd=d.transform
with rasterio.open(tif) as d:
    tr=d.transform; tiff=d.read(1);tags=d.tags();tif_bounds=list(d.bounds); area=d.tags().get('AREA_OR_POINT');crs=str(d.crs)
assert np.array_equal(wat,tiff)
corner=from_origin(att['ProjectionMinLongitude'],att['ProjectionMaxLatitude'],att['ProjectionResolution'],att['ProjectionResolution'])
# This grid is an explicit what-if. The team response does not specify every cell boundary or confirm the rounded attribute as exact.
r=0.003372
center_exact=from_origin(-105-r/2,45+r/2,r,r)
corner_exact=from_origin(-105,45,r,r)
frames={'gdal_netcdf_center_interpretation':gd, 'formula_center_assumption_exact_rounded_resolution':center_exact, 'formula_corner_assumption_exact_rounded_resolution':corner_exact, 'hypothetical_netcdf_corner_attr_resolution':corner, 'geotiff_transform':tr}
g=Geod(ellps='WGS84');rows=[]
for row,col in [(0,0),(2137,3447),(2211,3352),(2212,3352),(4447,4447)]:
    positions={key:list(t*(col+.5,row+.5)) for key,t in frames.items()};positions['stored_nc_coordinate']=[float(lon[col]),float(lat[row])]
    distances={key:float(g.inv(*pos,*positions['geotiff_transform'])[2]) for key,pos in positions.items() if key!='geotiff_transform'}
    rows.append({'row':row,'col':col,'centres':positions,'distance_from_geotiff_m':distances})
df=pd.read_csv(SAMPLES);assert len(df)==5661 and df[['x','y']].duplicated().sum()==0
assert not df[['x','y','s30','l30']].isna().any().any()
assert set(df.s30.unique()) <= {0,1} and set(df.l30.unique()) <= {0,1}
prior = supplement/'missouri_additional_flood_reference/noaa_viirs/netcdf_may30_5661_centres.csv'
old=pd.read_csv(prior);assert len(old)==len(df) and all(np.array_equal(old[c],df[c]) for c in ['x','y','s30','l30'])
x,y=Transformer.from_crs('EPSG:5070','EPSG:4326',always_xy=True).transform(df.x.to_numpy(),df.y.to_numpy())
assert np.allclose(x,old.longitude,rtol=0,atol=1e-12) and np.allclose(y,old.latitude,rtol=0,atol=1e-12)
arr={};summary={}
for name,t in frames.items():
    rr,cc=rowcol(t,x,y);rr=np.asarray(rr);cc=np.asarray(cc);assert ((rr>=0)&(rr<wat.shape[0])&(cc>=0)&(cc<wat.shape[1])).all()
    vv=wat[rr,cc]; qq=quality[rr,cc]; flood=(vv==15)|((vv>=101)&(vv<=200));z=pd.DataFrame({'row':rr,'col':cc,'code':vv,'quality':qq,'s30':df.s30,'l30':df.l30,'flood':flood})
    cells=z.groupby(['row','col','code','quality'],as_index=False).agg(n=('s30','size'),s30=('s30','sum'),l30=('l30','sum'),flood=('flood','first'))
    f=cells[cells.flood];arr[name]={'row':rr,'col':cc,'code':vv,'flood':flood}
    summary[name]={'unique_cells':len(cells),'cell_counts_by_code':{str(k):int(v) for k,v in cells.groupby('code').size().items()},'flood_cells':int(f.shape[0]),'flood_sample_centres':int(f.n.sum()),'flood_cells_with_any_s30_water':int((f.s30>0).sum()),'flood_cells_with_any_l30_water':int((f.l30>0).sum())}
comparisons={}
for name in frames:
    if name=='geotiff_transform':continue
    a=arr[name];b=arr['geotiff_transform'];comparisons[name+'_versus_tiff']={'different_containing_cell':int(((a['row']!=b['row'])|(a['col']!=b['col'])).sum()),'different_water_code':int((a['code']!=b['code']).sum()),'flood_status_disagreement':int((a['flood']!=b['flood']).sum()),'flood_in_both':int((a['flood']&b['flood']).sum())}
a=arr['formula_center_assumption_exact_rounded_resolution']; b=arr['gdal_netcdf_center_interpretation']
comparisons['formula_center_assumption_versus_gdal']={'different_containing_cell':int(((a['row']!=b['row'])|(a['col']!=b['col'])).sum()),'different_water_code':int((a['code']!=b['code']).sum()),'flood_status_disagreement':int((a['flood']!=b['flood']).sum())}
pointwise=pd.DataFrame({'longitude':x,'latitude':y})
for name,v in arr.items():
    for col in ['row','col','code','flood']: pointwise[name+'_'+col]=v[col]
pointwise.to_csv(OUT/'producer_formula_5661_pointwise.csv',index=False)
print('EXACT_FORMULA_EXAMPLE',-105+3352*r,45-2211*r)
result={'input':{'netcdf':nc.name,'geotiff':tif.name,'samples':SAMPLES.relative_to(supplement).as_posix(),'sample_sha256':hashlib.file_digest(SAMPLES.open('rb'),'sha256').hexdigest()},'water_attributes':att,'array_shape':wat.shape,'same_array':True,'geotiff_crs':crs,'geotiff_area_or_point':area,'transforms':{k:list(v) for k,v in frames.items()},'geotiff_bounds_edges':tif_bounds,'geotiff_last_cell_upper_left':list(tr*(4447,4447)),'netcdf_hypothetical_bounds_edges':list(rasterio.transform.array_bounds(*wat.shape,corner)),'stored_lon_first_last':[float(lon[0]),float(lon[-1])],'stored_lat_first_last':[float(lat[0]),float(lat[-1])],'grid_coordinate_results':rows,'summaries':summary,'comparisons':comparisons,'interpretation':'Formula-center and formula-corner are alternative pixel-support assumptions; the provider gave coordinate of the pixel but did not explicitly resolve the support boundaries or whether 0.003372 is exact or rounded. The corner and attribute resolution transform is a sensitivity calculation, not an independently confirmed producer grid. Raw stored NetCDF coordinate values and GDAL derived transform have different semantics from pixel boundaries. No differences here are measured sensor errors; a post-hoc geometric hypothesis cannot establish correct physical location or a bound on error. Data provider confirms equal upper-left as seen in screenshots but does not explicitly document per-cell centre semantics, exact grid increment or attribution to individual daily-composite observations.'}
(OUT/'producer_formula_comparison.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))


