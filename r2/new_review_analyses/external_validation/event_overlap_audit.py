from pathlib import Path
import json,hashlib
import pandas as pd, numpy as np, shapely
from shapely.geometry import shape,box
from shapely.ops import transform,unary_union
from pyproj import Transformer
base=Path(__file__).resolve().parent
root=base.parents[1]/'inputs/new_review_archives'
inputs=base.parents[1]/'inputs'
ra=root/'original_eight_event_utility.csv'
ids=['D5_2024_NEBRASKA_IOWA','N2024_191762_IOWA']
old=pd.read_csv(root/'consolidated_event_registry.csv');old=old[old.event_id.eq(ids[0])].iloc[0]
new=pd.read_csv(root/'noaa_blind_event_candidate_registry.csv');new=new[new.event_id.eq(ids[1])].iloc[0]
counties=json.loads((inputs/'counties_2025_semigeneral.geojson').read_text(encoding='utf8'))['features']
features={str(x['properties']['FIPS']).zfill(5):shape(x['geometry']) for x in counties}
project=Transformer.from_crs(4326,5070,always_xy=True).transform
u=transform(project,unary_union([features[str(i).zfill(5)] for i in pd.read_csv(root/'noaa_blind_event_candidate_counties.csv',dtype={'county_fips':str}).query('event_id == @ids[1]').county_fips]))
legacy=transform(project,shapely.segmentize(box(old.west,old.south,old.east,old.north),max_segment_length=0.01))
inter=u.intersection(legacy)
# This is an upper-bound footprint comparison: primary actual domain is clipped by common image coverage.
spatial=pd.DataFrame([dict(legacy_bbox_km2=legacy.area/1e6,primary_18_county_union_km2=u.area/1e6,county_union_intersect_legacy_bbox_km2=inter.area/1e6,county_union_intersection_pct=100*inter.area/u.area)])
spatial.to_csv(base/'footprint_upper_bound.csv',index=False)
noaa=pd.read_csv(root/'noaa_blind_event_candidate_counties.csv',dtype={'county_fips':str});nc=noaa[noaa.event_id.eq(ids[1])].copy()
legacycount=pd.read_csv(root/'event_county_linkage.csv',dtype={'county_fips':str});lc=legacycount[legacycount.event_id.eq(ids[0])]
same=nc.merge(lc[['county_fips','bbox_intersection_fraction']],on='county_fips')
same.to_csv(base/'overlapping_candidate_counties.csv',index=False)
d=pd.read_parquet(inputs/'primary_500m_cells.parquet',columns=['event_id','x_index','y_index','x_center_m','y_center_m','strict_common_valid_coverage','strict_common_valid_pixel_count'])
d=d[d.event_id.isin(ids)&d.strict_common_valid_coverage.ge(.95)&d.strict_common_valid_pixel_count.gt(0)].copy().reset_index(drop=True)
active=sorted(set(lc.county_fips)|set(nc.county_fips))
pairs=[(f,transform(project,features[f])) for f in active if f in features]
fips=np.array([x[0] for x in pairs]);tree=shapely.STRtree([x[1] for x in pairs])
ix=tree.query(shapely.points(d.x_center_m.to_numpy(),d.y_center_m.to_numpy()),predicate='intersects')
joins=pd.DataFrame({'row':ix[0],'fips':fips[ix[1]]}).sort_values(['row','fips']).drop_duplicates('row')
d['county_fips']=pd.Series(np.arange(len(d))).map(joins.set_index('row').fips).to_numpy()
# Restrict to original event-linked candidate counties before comparing.
d=d[((d.event_id.eq(ids[0]))&d.county_fips.isin(lc.county_fips))|((d.event_id.eq(ids[1]))&d.county_fips.isin(nc.county_fips))]
counts=d.groupby(['event_id','county_fips']).size().rename('accepted_500m_cell_count').reset_index()
counts.to_csv(base/'accepted_cells_by_county.csv',index=False)
first=counts[counts.event_id.eq(ids[0])];second=counts[counts.event_id.eq(ids[1])]
common=first.merge(second,on='county_fips',suffixes=('_legacy','_primary'))
lo=pd.read_csv(root/'external_event_county_outcomes.csv',dtype={'county_fips':str});po=pd.read_csv(root/'primary_external_event_county_outcomes.csv',dtype={'county_fips':str})
lo=lo[lo.event_id.eq(ids[0])];po=po[po.event_id.eq(ids[1])]
vals=['county_fips','county_name','rma_record_count','rma_indemnity_usd','rma_loss_months','rma_cause_codes','noaa_event_ids']
common=common.merge(lo[vals],on='county_fips').merge(po[vals],on='county_fips',suffixes=('_legacy','_primary'))
common.to_csv(base/'shared_accepted_county_outcomes.csv',index=False)
audubon=lo[lo.county_fips.eq('19009')][vals].merge(po[po.county_fips.eq('19009')][vals],on='county_fips',suffixes=('_legacy','_primary'))
assert len(audubon)==1
assert audubon.iloc[0].rma_record_count_legacy==audubon.iloc[0].rma_record_count_primary==5
assert np.isclose(audubon.iloc[0].rma_indemnity_usd_legacy,audubon.iloc[0].rma_indemnity_usd_primary)
assert '19009' not in set(first.county_fips) and '19009' in set(second.county_fips)
audubon.to_csv(base/'audubon_archived_linkage.csv',index=False)
v=pd.read_csv(ra);v=v[(v.score.eq('agreement_weighted_score'))&np.isclose(v.budget_fraction,.2)&v.capture_lift_over_random.notna()]
print('AWC rows',v.shape, v.columns.tolist())
assert len(v)==8
assert all(event in set(v.event_id) for event in ids)
assert np.isclose(v.capture_lift_over_random.mean(),1.6312567776655138)
v.to_csv(base/'original_eight_event_awc_lifts.csv',index=False)
sensitivity=pd.DataFrame([dict(scenario='eight_original',events=8,mean_lift=v.capture_lift_over_random.mean()),*[dict(scenario='omit_'+event,events=7,mean_lift=v.loc[~v.event_id.eq(event),'capture_lift_over_random'].mean()) for event in ids]])
sensitivity.to_csv(base/'paired_event_omission_lifts.csv',index=False)
inputfiles=[root/'consolidated_event_registry.csv',root/'noaa_blind_event_candidate_registry.csv',
 root/'noaa_blind_event_candidate_counties.csv',root/'event_county_linkage.csv',
 root/'external_event_county_outcomes.csv',root/'primary_external_event_county_outcomes.csv',
 inputs/'primary_500m_cells.parquet',inputs/'counties_2025_semigeneral.geojson',ra]
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputfiles}
manifest={'files_sha256':hashes,'geographic_crs':'EPSG:4326','area_and_grid_crs':'EPSG:5070',
 'box_transform':'WGS84 box edges densified to <=0.01 degree before transformation',
 'spatial_scope':'Intersection between registered legacy geographic bbox and union of 18 pre-imagery primary county polygons, not the intersection of actual product footprints or event flood extent.',
 'county_scope':'95% strict common-valid accepted 500m cell centres assigned to event-linked counties; actual end-point sample population, not meteorological independence.',
 'omit_scope':'Event-equal arithmetic mean at fixed 20% budget, selecting already-computed event values; post hoc sensitivity without inferential claim.'}
(base/'event_overlap_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('Bounding comparison',spatial.to_string(index=False))
print('County linked',same.to_string(index=False))
print('accepted counts by event',counts.groupby('event_id').size().to_dict())
print('shared accepted counties and outcomes',common.to_string(index=False))
print('leave-one-out',sensitivity.to_string(index=False))

