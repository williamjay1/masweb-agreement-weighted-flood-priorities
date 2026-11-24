"""Summarize extracted-domain support retention and candidate-county cell counts.

Denominators cover the paired-product extracted 500 m cells with positive eligible
pixel counts. They are not complete county-area or whole-county cropland shares.
County assignment duplicates the original boundary point-in-polygon rule.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

root=Path(__file__).resolve().parent
inputs=root/'inputs'
out=root/'results'
out.mkdir(exist_ok=True)
events=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN',
        'N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
cells=pd.read_parquet(inputs/'primary_500m_cells.parquet',columns=['event_id',
  'eligible_pixel_count','strict_common_valid_coverage','strict_common_valid_pixel_count',
  'x_center_m','y_center_m'])
cells=cells[cells.event_id.isin(events)&cells.eligible_pixel_count.gt(0)].copy()
cells['accepted']=cells.strict_common_valid_coverage.ge(.95)&cells.strict_common_valid_pixel_count.gt(0)
assert cells[cells.accepted].shape[0]==44510
ref=pd.read_csv(inputs/'county_scores_and_selections.csv',dtype={'county_fips':str})
ref=ref[ref.threshold.eq(.95)&ref.event_id.isin(events)].copy()
assert len(ref)==37
states=set(ref.county_fips.str[:2])
project=Transformer.from_crs(4326,5070,always_xy=True).transform
features=json.loads((inputs/'counties_2025_semigeneral.geojson').read_text(encoding='utf8'))['features']
pairs=[(str(f['properties']['FIPS']).zfill(5),transform(project,shape(f['geometry'])))
       for f in features if str(f['properties']['FIPS']).zfill(5)[:2] in states]
fips=np.asarray([p[0] for p in pairs]);tree=shapely.STRtree([p[1] for p in pairs])
county_rows=[];event_rows=[]
for event in events:
    full=cells[cells.event_id.eq(event)].copy();accepted=full[full.accepted].copy().reset_index(drop=True)
    ix=tree.query(shapely.points(accepted.x_center_m.to_numpy(),accepted.y_center_m.to_numpy()),predicate='intersects')
    joins=pd.DataFrame({'row':ix[0],'fips':fips[ix[1]]}).sort_values(['row','fips']).drop_duplicates('row')
    accepted['county_fips']=pd.Series(np.arange(len(accepted))).map(joins.set_index('row').fips)
    candidates=ref[ref.event_id.eq(event)].copy()
    counts=accepted.groupby('county_fips',dropna=False).agg(accepted_cells=('county_fips','size'),
         eligible_pixels=('eligible_pixel_count','sum'),strict_common_valid_pixels=('strict_common_valid_pixel_count','sum'))
    for row in candidates.itertuples():
        assert row.county_fips in counts.index, (event,row.county_fips)
        v=counts.loc[row.county_fips]
        # County eligibility sums must reproduce the source aggregation used in the manuscript.
        assert int(v.eligible_pixels)==int(row.eligible_pixel_count)
        assert int(v.strict_common_valid_pixels)==int(row.strict_common_valid_pixel_count)
        county_rows.append({'event_id':event,'county_fips':row.county_fips,
            'county_name':row.county_name,'accepted_500m_cells':int(v.accepted_cells),
            'eligible_30m_pixels_in_accepted_cells':int(v.eligible_pixels),
            'common_valid_30m_pixels_in_accepted_cells':int(v.strict_common_valid_pixels)})
    outside=accepted[~accepted.county_fips.isin(set(candidates.county_fips))]
    total_cells=len(full); keep_cells=len(accepted)
    total_pixels=int(full.eligible_pixel_count.sum());keep_pixels=int(accepted.eligible_pixel_count.sum())
    assert keep_cells==sum(x['accepted_500m_cells'] for x in county_rows if x['event_id']==event)+len(outside)
    event_rows.append({'event_id':event,'extracted_candidate_500m_cells':total_cells,
       'accepted_500m_cells':keep_cells,'accepted_cell_fraction':keep_cells/total_cells,
       'eligible_30m_pixels_in_candidate_cells':total_pixels,
       'eligible_30m_pixels_in_accepted_cells':keep_pixels,'eligible_pixel_fraction':keep_pixels/total_pixels,
       'accepted_cells_outside_fixed_candidate_counties':len(outside),
       'accepted_cells_missing_county_assignment':int(accepted.county_fips.isna().sum())})
pd.DataFrame(event_rows).to_csv(out/'support_retention_event.csv',index=False)
pd.DataFrame(county_rows).to_csv(out/'accepted_cells_by_county.csv',index=False)
print(pd.DataFrame(event_rows).to_string(index=False))
print('Candidate county rows:',len(county_rows))
