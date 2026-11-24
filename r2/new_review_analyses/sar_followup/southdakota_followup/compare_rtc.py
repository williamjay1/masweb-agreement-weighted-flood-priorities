from pathlib import Path
import requests,json,hashlib,argparse
import numpy as np,pandas as pd,rasterio
from rasterio.warp import reproject,Resampling
p=argparse.ArgumentParser();p.add_argument('--derived-root',type=Path,required=True);p.add_argument('--cells',type=Path,required=True);p.add_argument('--raw-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);a.raw_root.mkdir(parents=True,exist_ok=True)
e='N2023_180114_SOUTHDAKOTA';bbox=[-99.6,44.15,-97.25,45.1]
q={'collections':['sentinel-1-rtc'],'bbox':bbox,'datetime':'2023-04-09T00:00:00Z/2023-04-11T23:59:59Z','limit':100};res=requests.post('https://planetarycomputer.microsoft.com/api/stac/v1/search',json=q,timeout=60);res.raise_for_status();j=res.json();assert len(j['features'])==2
meta=a.raw_root/'planetary_rtc_20230409_20230411_search.json'
if not meta.exists():meta.write_text(json.dumps({'query':q,'result':j},indent=2),encoding='utf8')
feat=sorted(j['features'],key=lambda x:x['properties']['datetime']);assert all(x['properties']['sat:relative_orbit']==12 for x in feat)
sel=pd.read_parquet(a.cells);sel=sel[(sel.event_id==e)&sel.strict_qualified].copy();assert len(sel)==2628
sp=a.derived_root/'blind_opera_pair_states'/e/(e+'_S30_state_EPSG5070_30m.tif');lp=a.derived_root/'blind_opera_pair_states'/e/(e+'_L30_state_EPSG5070_30m.tif');ep=a.derived_root/'blind_eligibility'/e/(e+'_lagged_eligibility_EPSG5070_30m.tif')
with rasterio.open(sp) as s,rasterio.open(lp) as l,rasterio.open(ep) as ag:
 assert s.crs==l.crs==ag.crs and s.transform==l.transform==ag.transform and s.shape==l.shape==ag.shape
 tr=s.transform;crs=s.crs;shape=s.shape;sg=s.read(2);sq=s.read(4);lg=l.read(2);lq=l.read(4);elig=ag.read(6)==1
 ok=elig&(sg<=1)&(lg<=1)&((sq&127)==0)&((lq&127)==0)&((sq&128)!=0)&((lq&128)!=0)
 rr,cc=np.where(ok);xi=np.floor((tr.c+(cc+.5)*tr.a)/500).astype('int32');yi=np.floor((tr.f+(rr+.5)*tr.e)/500).astype('int32')
 pix=pd.DataFrame({'r':rr.astype('int32'),'c':cc.astype('int32'),'x_index':xi,'y_index':yi,'s30':sg[rr,cc],'l30':lg[rr,cc]}).merge(sel[['x_index','y_index','strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count']],on=['x_index','y_index'],how='inner',validate='many_to_one')
 check=pix.groupby(['x_index','y_index']).agg(n=('s30','size'),s=('s30','sum'),l=('l30','sum')).reset_index().merge(sel,on=['x_index','y_index'],validate='one_to_one')
 assert len(check)==2628 and (check.n==check.strict_common_valid_pixel_count).all() and (check.s==check.strict_s30_water_pixel_count).all() and (check.l==check.strict_l30_water_pixel_count).all()
 print('original pixel totals',len(pix),pix.s30.sum(),pix.l30.sum(),flush=True)
 del sg,sq,lg,lq,elig,ok,rr,cc
# Asset metadata JSON has unsigned URLs only; short-lived token is fetched in memory and never logged.
token=requests.get('https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel1euwestrtc/sentinel1-grd-rtc',timeout=30).json()['token'];v=[]
for i,f in enumerate(feat):
 path=a.out/(f'scene_{i+1}_vv_30m.tif')
 if not path.exists():
  dst=np.full(shape,-9999,dtype='float32');url=f['assets']['vv']['href']+'?'+token
  print('warping scene',i+1,f['id'],flush=True)
  with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_HTTP_MAX_RETRY='4',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tiff', GDAL_CACHEMAX=256000000):
   with rasterio.open(url) as src:
    reproject(rasterio.band(src,1),dst,src_transform=src.transform,src_crs=src.crs,src_nodata=src.nodata,dst_transform=tr,dst_crs=crs,dst_nodata=-9999,resampling=Resampling.average,num_threads=2)
  with rasterio.open(path,'w',driver='GTiff',height=shape[0],width=shape[1],count=1,dtype='float32',crs=crs,transform=tr,nodata=-9999,compress='deflate',tiled=True) as out:out.write(dst,1)
  del dst
 with rasterio.open(path) as src:
  arr=src.read(1);v.append(arr[pix.r.to_numpy(),pix.c.to_numpy()]);del arr
print('warps completed',flush=True)
stack=np.stack(v);good=np.isfinite(stack)&(stack>0);n=good.sum(axis=0);vv=np.divide(np.where(good,stack,0).sum(axis=0),n,out=np.full(len(n),np.nan),where=n>0);valid=np.isfinite(vv)&(vv>0);db=10*np.log10(vv[valid]);common=pix[valid].copy();common['vv_db']=db
print('common',len(common),'orig',len(pix),'overlap two source scenes',int((n==2).sum()),flush=True)
rows=[]
for t in [-19.,-17.,-15.]:
 b=common.vv_db.to_numpy()<t
 for sensor in ('s30','l30'):
  z=common[sensor].to_numpy().astype(bool)
  tp=int((z&b).sum());fp=int((z&~b).sum());fn=int((~z&b).sum());tn=int((~z&~b).sum());union=tp+fp+fn
  rows.append({'vv_threshold_db':t,'sensor':sensor,'common_pixels':len(common),'optical_water':int(z.sum()),'radar_dark_candidates':int(b.sum()),'both':tp,'optical_only':fp,'sar_only':fn,'neither':tn,'intersection_over_union':tp/union if union else None})
res=pd.DataFrame(rows);res.to_csv(a.out/'southdakota_vv_dark_candidate_comparison.csv',index=False);common.groupby(['x_index','y_index']).agg(common_pixels=('s30','size'),s30_water=('s30','sum'),l30_water=('l30','sum')).to_csv(a.out/'southdakota_common_cell_summary.csv');print(res.to_string(index=False),flush=True)
manifest={'protocol':'analysis_protocol.md','event':e,'source':'Microsoft Planetary Computer sentinel-1-rtc','source_scenes':[{ 'id':f['id'],'datetime':f['properties']['datetime'],'unsigned_vv_url':f['assets']['vv']['href'],'metadata_checksum':f['assets']['vv'].get('file:checksum')} for f in feat],'original_common_optical_pixels':len(pix),'sar_optical_common_pixels':len(common),'sar_valid_cells':int(common.groupby(['x_index','y_index']).ngroups),'source_overlap_pixel_count':int((n==2).sum()),'temporal_and_interpretive_limits':'dark backscatter is not flood truth; no local calibration, snow/ice and bare soil can confound; VV thresholds from prior published study, gamma0 transfer unverified','warp':'average 10m linear power to original 30m grid, average in valid overlap, 10 log10 convert','predeclared_thresholds_db':[-19,-17,-15]}
(a.out/'southdakota_rtc_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
