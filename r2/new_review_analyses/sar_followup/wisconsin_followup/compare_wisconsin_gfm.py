from pathlib import Path
import json,hashlib,argparse
import numpy as np,pandas as pd,rasterio
from rasterio.warp import reproject,Resampling
from scipy.stats import spearmanr
parser=argparse.ArgumentParser(description='Reproduce Wisconsin GFM versus optical product comparison')
parser.add_argument('--derived-root',type=Path,required=True,help='Root containing blind_opera_pair_states and blind_eligibility')
parser.add_argument('--gfm-root',type=Path,required=True,help='Directory containing source STAC search JSON and four TIFF files')
parser.add_argument('--extra-root',type=Path,required=True,help='Directory containing GFM flood layers')
parser.add_argument('--cells',type=Path,required=True,help='Frozen primary 500m cell parquet')
parser.add_argument('--output',type=Path,required=True,help='Directory for derived outputs')
args=parser.parse_args();here=args.output;here.mkdir(parents=True,exist_ok=True);root=args.derived_root;raw=args.gfm_root
e='N2023_179829_WISCONSIN';date='2023-04-15T23:58:33Z/2023-04-15T23:58:58Z'
selpath=args.cells
sel=pd.read_parquet(selpath);sel=sel[(sel.event_id==e)&sel.strict_qualified].copy()
assert len(sel)==221
sp=root/'blind_opera_pair_states'/e/(e+'_S30_state_EPSG5070_30m.tif');lp=root/'blind_opera_pair_states'/e/(e+'_L30_state_EPSG5070_30m.tif');ep=root/'blind_eligibility'/e/(e+'_lagged_eligibility_EPSG5070_30m.tif')
with rasterio.open(sp) as s,rasterio.open(lp) as l,rasterio.open(ep) as ag:
 assert s.crs==l.crs==ag.crs and s.transform==l.transform==ag.transform and s.shape==l.shape==ag.shape
 tr=s.transform;crs=s.crs;shape=s.shape
 sg=s.read(2);sq=s.read(4);lg=l.read(2);lq=l.read(4);elig=ag.read(6)==1
 ok=elig&(sg<=1)&(lg<=1)&((sq&127)==0)&((lq&127)==0)&((sq&128)!=0)&((lq&128)!=0)
 rr,cc=np.where(ok);xi=np.floor((tr.c+(cc+.5)*tr.a)/500).astype('int32');yi=np.floor((tr.f+(rr+.5)*tr.e)/500).astype('int32')
 pix=pd.DataFrame({'r':rr.astype('int32'),'c':cc.astype('int32'),'x_index':xi,'y_index':yi,'s30':sg[rr,cc],'l30':lg[rr,cc]})
 pix=pix.merge(sel[['x_index','y_index','strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count']],on=['x_index','y_index'],how='inner',validate='many_to_one')
 check=pix.groupby(['x_index','y_index']).agg(n=('s30','size'),s=('s30','sum'),l=('l30','sum')).reset_index().merge(sel,on=['x_index','y_index'],validate='one_to_one')
 assert len(check)==221 and (check.n==check.strict_common_valid_pixel_count).all() and (check.s==check.strict_s30_water_pixel_count).all() and (check.l==check.strict_l30_water_pixel_count).all()
 print('ORIGINAL',len(pix),int(pix.s30.sum()),int(pix.l30.sum()),flush=True)
 del sg,sq,lg,lq,elig,ok,rr,cc
meta=json.loads((raw/(e+'_search.json')).read_text(encoding='utf8'));features=[f for f in meta['features'] if f['id'] in {'ENSEMBLE_FLOOD_20230415T235833_VV_NA020M_E084N042T3','ENSEMBLE_FLOOD_20230415T235833_VV_NA020M_E087N042T3','ENSEMBLE_FLOOD_20230415T235858_VV_NA020M_E084N042T3','ENSEMBLE_FLOOD_20230415T235858_VV_NA020M_E087N042T3'}];assert len(features)==4 and all(f['properties']['processing:version']=='GFM v3.1.0' for f in features)
rows_conf=[];rows_cell=[];stats=[];scene_info=[]
for category in ['ensemble_water_extent','ensemble_flood_extent']:
 vectors=[]
 for f in features:
  path=(raw if category=='ensemble_water_extent' else args.extra_root)/(f['id']+'__'+category+'.tif')
  with rasterio.open(path) as ds:
   assert ds.nodata==255 and ds.count==1
   dst=np.full(shape,255,dtype='uint8')
   reproject(source=rasterio.band(ds,1),destination=dst,src_transform=ds.transform,src_crs=ds.crs,src_nodata=255,dst_transform=tr,dst_crs=crs,dst_nodata=255,resampling=Resampling.nearest,num_threads=2,init_dest_nodata=True)
   v=dst[pix.r.to_numpy(),pix.c.to_numpy()];assert np.isin(v,[0,1,255]).all();vectors.append(v)
   scene_info.append({'item':f['id'],'category':category,'datetime':f['properties']['datetime'],'valid_samples':int((v!=255).sum()),'positive_samples':int((v==1).sum()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'url':f['assets'][category]['href']})
   del dst
 stack=np.stack(vectors);has0=(stack==0).any(axis=0);has1=(stack==1).any(axis=0);conflict=has0&has1;radar=np.where(conflict,255,np.where(has1,1,np.where(has0,0,255))).astype('uint8');pix['radar']=radar;del stack
 common=pix[pix.radar!=255].copy();print(category,'VALID',len(common),'POSITIVE',int((common.radar==1).sum()),'CONFLICTS',int(conflict.sum()),'OPTICAL',int(common.s30.sum()),int(common.l30.sum()),flush=True)
 for sensor in ['s30','l30']:
  for x in [0,1]:
   for y in [0,1]:rows_conf.append({'radar_layer':category,'optical_sensor':sensor,'optical_water':x,'radar_water':y,'pixel_count':int(((common[sensor]==x)&(common.radar==y)).sum()),'total_common_pixels':len(common)})
 c=common.groupby(['x_index','y_index']).agg(common_pixels=('radar','size'),s30_water_pixels=('s30','sum'),l30_water_pixels=('l30','sum'),radar_water_pixels=('radar','sum')).reset_index()
 c=c.merge(sel[['x_index','y_index','strict_common_valid_pixel_count']],on=['x_index','y_index'],validate='one_to_one');c['radar_fraction']=c.radar_water_pixels/c.common_pixels;c['s30_fraction']=c.s30_water_pixels/c.common_pixels;c['l30_fraction']=c.l30_water_pixels/c.common_pixels;c['radar_coverage']=c.common_pixels/c.strict_common_valid_pixel_count;c['radar_layer']=category
 rows_cell.append(c)
 for mincoverage in [0,.95,1]:
  z=c[c.radar_coverage>=mincoverage].copy();print('coverage',mincoverage,'cells',len(z),'radar positive cells',int((z.radar_water_pixels>0).sum()),flush=True)
  for sensor in ['s30','l30']:
   n=len(z);k=int(np.ceil(.2*n));z=z.sort_values(['x_index','y_index']);v=z[sensor+'_fraction'].to_numpy();rad=z.radar_fraction.to_numpy();order=np.lexsort((z.y_index,z.x_index,-v));selidx=order[:k];overlap='undefined';rho='undefined';capture='undefined'
   if len(np.unique(v))>1 and len(np.unique(rad))>1:rho=float(spearmanr(v,rad).statistic)
   if rad.sum()>0:capture=float(rad[selidx].sum()/rad.sum())
   stats.append({'radar_layer':category,'coverage_min':mincoverage,'sensor':sensor,'cells':n,'k':k,'radar_positive_cells':int((rad>0).sum()),'optical_positive_cells':int((v>0).sum()),'spearman':rho,'coordinate_top20_radar_fraction_capture':capture,'warning':'post hoc, weighted radar-positive water fraction capture, not probability or validation of flood truth; shared coordinate tie ordering'})
pd.DataFrame(rows_conf).to_csv(here/'wisconsin_common_pixel_confusion.csv',index=False);pd.concat(rows_cell).to_csv(here/'wisconsin_common_cell_summaries.csv',index=False);pd.DataFrame(stats).to_csv(here/'wisconsin_exploratory_cell_metrics.csv',index=False)
report={'event':e,'source':'Copernicus GFM v3.1.0 Sentinel-1 ensemble, archive V02','gmf_datetime_utc':date,'optical_s30_utc':'2023-04-14T17:08:49Z','optical_l30_utc':'2023-04-14T16:51:36Z','event_registered_window':['2023-04-11','2023-04-30'],'accepted_cells_original':len(sel),'joint_optical_eligible_pixels':len(pix),'scene_info':scene_info,'method':'Categorical 20m GFM rasters independently nearest-neighbor reprojected into the exact optical EPSG:5070 30m grid; retain only original eligible, strict-both-valid pixels inside original accepted 500m cells. Merge tiles from two nearby acquisition times spanning 25 seconds, treating any category conflict as missing. Compare each optical product against same radar mask.','limitations':['independent SAR observations, not ground truth','GFM water is flood plus historical reference water; auxiliary global surface water inputs overlap with optical land eligibility','GFM flood excludes reference water while optical DSWx maps water','SAR acquired approximately 31 hours after optical acquisitions; water and physical conditions can change substantially','one event, spatially correlated samples, different resolutions, no population uncertainty or superiority claim']}
(here/'wisconsin_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
