from pathlib import Path
import pandas as pd
base=Path(__file__).resolve().parent
p=base/'inputs/primary_500m_cells.parquet'
d=pd.read_parquet(p,columns=['event_id','x_index','y_index','strict_common_valid_coverage','strict_common_valid_pixel_count'])
ids=['D5_2024_NEBRASKA_IOWA','N2024_191762_IOWA']
d=d[d.event_id.isin(ids)&d.strict_common_valid_coverage.ge(.95)&d.strict_common_valid_pixel_count.gt(0)]
a,b=[d[d.event_id.eq(x)] for x in ids]
a1=set(map(tuple,a[['x_index','y_index']].to_numpy()));b1=set(map(tuple,b[['x_index','y_index']].to_numpy()))
assert len(a1)==len(a) and len(b1)==len(b)
result=pd.DataFrame([{'legacy_event':ids[0],'primary_event':ids[1],'legacy_accepted_cells':len(a1),'primary_accepted_cells':len(b1),'shared_accepted_cell_keys':len(a1&b1),'legacy_x_min':a.x_index.min(),'legacy_x_max':a.x_index.max(),'primary_x_min':b.x_index.min(),'primary_x_max':b.x_index.max()}]);result.to_csv(base/'results/iowa_legacy_accepted_cell_overlap.csv',index=False);print(result.to_string(index=False));print('This does not assess full event footprints or meteorological independence.')
