from pathlib import Path
import numpy as np,pandas as pd
here=Path(__file__).resolve().parent;src=here.parents[1]/'inputs'
scores=pd.read_csv(src/'county_scores_and_selections.csv',dtype={'county_fips':str})
outcomes=pd.read_csv(src/'primary_external_event_county_outcomes_normalized.csv',dtype={'county_fips':str})
h=scores.merge(outcomes[['event_id','county_fips','any_noaa_flood_record','noaa_flood_record_count']],on=['event_id','county_fips'],validate='many_to_one')
assert len(h)==111
assert (h.any_noaa_flood_record.fillna(False).astype(bool)==h.noaa_flood_record_count.fillna(0).gt(0)).all()
r=[]
for (threshold,event),g in h.groupby(['threshold','event_id']):
 y=g.any_noaa_flood_record.fillna(False).astype(float).to_numpy();assert y.sum()>0
 for score in ['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score']:
  w=g[score+'_selection_weight'].to_numpy();capture=float(w@y/y.sum());r.append({'threshold':threshold,'event_id':event,'score':score,'capture':capture,'lift':capture/.2})
d=pd.DataFrame(r); assert len(d)==60
pivot=d.pivot(index=['event_id','score'],columns='threshold',values='lift');assert np.allclose(pivot[.9],pivot[.95]) and np.allclose(pivot[.95],pivot[.99])
d.to_csv(here/'noaa_all_support_thresholds_events.csv',index=False)
d.groupby(['threshold','score'],as_index=False).agg(events=('event_id','size'),mean_lift=('lift','mean')).to_csv(here/'noaa_all_support_thresholds_summary.csv',index=False)
print(d.groupby(['threshold','score']).lift.mean().to_string())
