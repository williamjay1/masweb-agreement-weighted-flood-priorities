from pathlib import Path
import pandas as pd, numpy as np, hashlib
BASE=Path(__file__).resolve().parent
fixed=BASE/'inputs/hls_index_500m_cells.parquet'
dir=BASE/'inputs/otsu_cells'
events=['C2_2025_LOWER_OHIO','D3_2024_CENTRAL_INDIANA','D5_2024_NEBRASKA_IOWA']
allfixed=pd.read_parquet(fixed); rows=[]
for ev in events:
 a=allfixed[allfixed.event_id.eq(ev)].copy();b=pd.read_parquet(dir/f'{ev}_hls_index_500m_cells.parquet')
 j=a.merge(b,on=['event_id','x_index','y_index'],validate='one_to_one',suffixes=('_fixed','_otsu'))
 qual=j.four_chain_strict_qualified_fixed&j.four_chain_strict_qualified_otsu
 q=j[qual];da=q.four_chain_common_pixel_count_fixed;db=q.four_chain_common_pixel_count_otsu
 rows.append(dict(event_id=ev,common_qualified_500m_cells=int(qual.sum()),
  different_common_pixel_counts=int((da!=db).sum()),
  fraction_cells_different_common_pixel_counts=float((da!=db).mean()),
  fixed_pixels=int(da.sum()),otsu_pixels=int(db.sum()),
  sum_absolute_pixel_count_differences=int((da-db).abs().sum()),
  exact_pixel_overlap_known=False))
pd.DataFrame(rows).to_csv(BASE/'results/otsu_common_support_limitation.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))

