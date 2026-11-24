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
meta=json.loads((raw/(e+'_search.json')).read_text(encoding='utf8'))
ids={'ENSEMBLE_FLOOD_20230415T235833_VV_NA020M_E084N042T3','ENSEMBLE_FLOOD_20230415T235833_VV_NA020M_E087N042T3','ENSEMBLE_FLOOD_20230415T235858_VV_NA020M_E084N042T3','ENSEMBLE_FLOOD_20230415T235858_VV_NA020M_E087N042T3'}
features=[f for f in meta['features'] if f['id'] in ids];assert len(features)==4
arrays=[]
for f in features:
 row=[]
 for cat in ['ensemble_water_extent','advisory_flags','exclusion_mask']:
  source=(raw if cat=='ensemble_water_extent' else args.extra_root)/(f['id']+'__'+cat+'.tif')
  with rasterio.open(source) as ds:
   dst=np.full(shape,255,dtype='uint8');reproject(source=rasterio.band(ds,1),destination=dst,src_transform=ds.transform,src_crs=ds.crs,src_nodata=255,dst_transform=tr,dst_crs=crs,dst_nodata=255,resampling=Resampling.nearest,num_threads=2,init_dest_nodata=True)
   row.append(dst[pix.r.to_numpy(),pix.c.to_numpy()]);del dst
 arrays.append(row)
a=np.asarray(arrays);w=a[:,0,:];q=a[:,1,:];x=a[:,2,:];v=w!=255
for label,code in [('quality',q),('exclusion',x)]:
 print(label,'by pixel values with contributing water', {int(k):int(np.any(v&(code==k),axis=0).sum()) for k in np.unique(code[v])},flush=True)
qflag=np.any(v&(q!=0)&(q!=255),axis=0);qmiss=~np.any(v&(q!=255),axis=0);ex=np.any(v&(x==1),axis=0); water=np.any(v&(w==1),axis=0)
pix['any_advisory']=qflag;pix['quality_missing']=qmiss;pix['any_exclusion']=ex;pix['gfm_water']=water
print('flagged',int(qflag.sum()),'missing',int(qmiss.sum()),'excluded',int(ex.sum()),'water',int(water.sum()),'water flagged',int((water&qflag).sum()),flush=True)
rows=[]
for mask_name,mask in [('all',np.ones(len(pix),dtype=bool)),('exclude_advisory',~qflag&~qmiss),('exclude_mask_1',~ex),('both',~qflag&~qmiss&~ex)]:
 z=pix[mask]; print(mask_name,'n',len(z),'S',int(z.s30.sum()),'L',int(z.l30.sum()),'GFM',int(z.gfm_water.sum()),flush=True)
 for sensor in ['s30','l30']:
  for i in [0,1]:
   for j in [0,1]: rows.append({'domain':mask_name,'sensor':sensor,'optical_water':i,'gfm_water':j,'n':int(((z[sensor]==i)&(z.gfm_water==j)).sum()),'domain_n':len(z)})
pd.DataFrame(rows).to_csv(here/'wisconsin_qa_sensitivity.csv',index=False)
