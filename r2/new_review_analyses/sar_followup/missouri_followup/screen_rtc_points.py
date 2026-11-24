from pathlib import Path
import requests,json,argparse,numpy as np,pandas as pd,rasterio
from rasterio.transform import rowcol
from rasterio.windows import Window
from pyproj import Transformer
P=argparse.ArgumentParser();P.add_argument('--output',type=Path,required=True);P.add_argument('--raw',type=Path,required=True);P.add_argument('--derived-root',type=Path,required=True);P.add_argument('--cells',type=Path,required=True);A=P.parse_args();out=A.output;out.mkdir(parents=True,exist_ok=True);raw=A.raw;raw.mkdir(parents=True,exist_ok=True)
q={'collections':'sentinel-1-rtc','bbox':'-94.1241,36.4828,-92.5184,37.8490','datetime':'2025-05-23T00:00:00Z/2025-06-06T23:59:59Z','limit':100};j=requests.get('https://planetarycomputer.microsoft.com/api/stac/v1/search',params=q,timeout=30).json();(raw/'missouri_rtc_stac.json').write_text(json.dumps(j,indent=2),encoding='utf8') if not (raw/'missouri_rtc_stac.json').exists() else None
e='N2025_202615_MISSOURI';root=A.derived_root;sel=pd.read_parquet(A.cells);sel=sel[(sel.event_id==e)&sel.strict_qualified]
with rasterio.open(root/'blind_opera_pair_states'/e/(e+'_S30_state_EPSG5070_30m.tif')) as s,rasterio.open(root/'blind_opera_pair_states'/e/(e+'_L30_state_EPSG5070_30m.tif')) as l,rasterio.open(root/'blind_eligibility'/e/(e+'_lagged_eligibility_EPSG5070_30m.tif')) as ag:
 t=s.transform; sg=s.read(2);lg=l.read(2);sq=s.read(4);lq=l.read(4);ok=(ag.read(6)==1)&(sg<=1)&(lg<=1)&((sq&127)==0)&((lq&127)==0)&((sq&128)!=0)&((lq&128)!=0);r,c=np.where(ok);x=t.c+(c+.5)*t.a;y=t.f+(r+.5)*t.e;df=pd.DataFrame({'x':x,'y':y,'x_index':np.floor(x/500).astype('int32'),'y_index':np.floor(y/500).astype('int32'),'s30':sg[r,c],'l30':lg[r,c]}).merge(sel[['x_index','y_index']],on=['x_index','y_index'],validate='many_to_one');assert len(df)==5661
print('items',len(j['features']),flush=True)
for f in j['features']:
 for band in ['vv','vh']:
  sas=requests.get('https://planetarycomputer.microsoft.com/api/sas/v1/sign',params={'href':f['assets'][band]['href']},timeout=30).json()['href'];
  with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tiff',VSI_CACHE='TRUE'):
   with rasterio.open(sas) as ds:
    tr=Transformer.from_crs(5070,ds.crs,always_xy=True);xx,yy=tr.transform(df.x.to_numpy(),df.y.to_numpy());rr,cc=rowcol(ds.transform,xx,yy);rr=np.array(rr);cc=np.array(cc);valid=(rr>=0)&(cc>=0)&(rr<ds.height)&(cc<ds.width); br=rr//512;bc=cc//512;vals=np.full(len(df),np.nan)
    for ky in set(zip(br[valid],bc[valid])):
     inds=np.where(valid&(br==ky[0])&(bc==ky[1]))[0];r0,c0=ky[0]*512,ky[1]*512;h=min(512,ds.height-r0);w=min(512,ds.width-c0);z=ds.read(1,window=Window(c0,r0,w,h));v=z[rr[inds]-r0,cc[inds]-c0];vals[inds]=np.where((v>0)&(v!=ds.nodata),v,np.nan)
    name=f['id']+'_'+band;df[name]=vals;print(name,'valid',int(np.isfinite(vals).sum()),flush=True)
df.to_csv(out/'rtc_may26_point_samples.csv',index=False)
