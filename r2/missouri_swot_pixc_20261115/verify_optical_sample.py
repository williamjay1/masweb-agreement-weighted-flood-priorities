from pathlib import Path
import json
import numpy as np
import pandas as pd
import rasterio

root=Path('external/data/remote_sensing_sci_novelty_audit/candidate3_agricultural_hazard_cascade/revision_geocarto_v4/data/derived/blind_opera_pair_states/N2025_202615_MISSOURI')
s=pd.read_csv('external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv')
xy=list(zip(s.x,s.y)); result=[]
for sensor in ('S30','L30'):
 path=root/f'N2025_202615_MISSOURI_{sensor}_state_EPSG5070_30m.tif'
 with rasterio.open(path) as ds:
  vals=np.array([v[0] for v in ds.sample(xy,indexes=2)])
  rr,cc=rasterio.transform.rowcol(ds.transform,s.x.to_numpy(),s.y.to_numpy())
  x,y=rasterio.transform.xy(ds.transform,rr,cc,offset='center')
  result.append(dict(sensor=sensor,path=str(path),crs=str(ds.crs),transform=list(ds.transform),
    sampled=len(s),matching_values=int(np.count_nonzero(vals==s[sensor.lower()].to_numpy())),
    max_x_center_error=float(np.max(np.abs(np.asarray(x)-s.x))),
    max_y_center_error=float(np.max(np.abs(np.asarray(y)-s.y)))))
out=Path(__file__).parent/'outputs'/'optical_sample_verification.json';out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
