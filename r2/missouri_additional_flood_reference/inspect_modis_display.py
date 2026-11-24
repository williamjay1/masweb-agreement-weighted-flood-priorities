from pathlib import Path
import math,json,hashlib,requests
import pandas as pd
from pyproj import Transformer
from PIL import Image
from io import BytesIO
base=Path('external/analysis/Geocarto_R2_20261115/missouri_flood_reference_20261115/modis_display');base.mkdir(parents=True,exist_ok=True)
raw=Path('external/data/Geocarto_R2_20261115/raw/missouri_flood_gibs_20261115');raw.mkdir(parents=True,exist_ok=True)
p=Path('external/analysis/Geocarto_R2_20261115/missouri_sar_continued_20261115/integration/work/supplementary_analysis/new_review_analyses/sar_followup/missouri_followup/rtc_may26_point_samples.csv');df=pd.read_csv(p);assert len(df)==5661
lon,lat=Transformer.from_crs(5070,4326,always_xy=True).transform(df.x.to_numpy(),df.y.to_numpy());res=0.5625/256; span=512*res
df['lon']=lon;df['lat']=lat;df['tc']=[math.floor((x+180)/span) for x in lon];df['tr']=[math.floor((90-y)/span) for y in lat];df['pc']=[math.floor((x+180)/res)%512 for x in lon];df['pr']=[math.floor((90-y)/res)%512 for y in lat];print('tile layout',df.groupby(['tr','tc']).size().to_dict(),flush=True)
sess=requests.Session();meta=[]
for day in ['2025-05-24','2025-05-25','2025-05-26','2025-05-27','2025-05-30']:
 for (row,col),idx in df.groupby(['tr','tc']).groups.items():
  url=f'https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/MODIS_Combined_Flood_1-Day/default/{day}/250m/8/{row}/{col}.png';f=raw/f'modis_1day_{day}_z8_r{row}_c{col}.png'
  if not f.exists():
   r=sess.get(url,timeout=45);r.raise_for_status();f.write_bytes(r.content)
  b=f.read_bytes();im=Image.open(BytesIO(b)).convert('RGBA')
  if im.size!=(512,512):raise ValueError('bad dimensions')
  for i in idx:
   rgba=im.getpixel((df.at[i,'pc'],df.at[i,'pr'])); df.at[i,'rgba_'+day]=','.join(map(str,rgba))
  meta.append({'date':day,'tile_row':int(row),'tile_col':int(col),'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'file':f.name})
 print(day,df['rgba_'+day].value_counts(dropna=False).to_dict(),flush=True)
(base/'tile_manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
df.to_csv(base/'modis_display_points.csv',index=False)
