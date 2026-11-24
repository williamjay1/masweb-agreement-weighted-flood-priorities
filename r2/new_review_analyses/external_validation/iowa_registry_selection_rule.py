from pathlib import Path
import pandas as pd
here=Path(__file__).resolve().parent
inp=here.parents[1]/'inputs/new_review_archives'
a=pd.read_csv(inp/'consolidated_event_registry.csv').query("event_id == 'D5_2024_NEBRASKA_IOWA'").iloc[0]
b=pd.read_csv(inp/'noaa_blind_event_candidate_registry.csv').query("event_id == 'N2024_191762_IOWA'").iloc[0]
area=lambda r: (r.east-r.west)*(r.north-r.south)
intersection=max(0,min(a.east,b.east)-max(a.west,b.west))*max(0,min(a.north,b.north)-max(a.south,b.south))
small=min(area(a),area(b));ratio=intersection/small
assert abs(ratio-0.03826254)<1e-7
assert max(pd.Timestamp(a.event_start),pd.Timestamp(b.event_start))<=min(pd.Timestamp(a.event_end),pd.Timestamp(b.event_end))
pd.DataFrame([{'legacy':a.event_id,'primary':b.event_id,'rectangle_intersection_degree2':intersection,'smaller_rectangle_degree2':small,'intersection_over_smaller':ratio,'temporal_gap_days':0,'exclusion_threshold':0.2}]).to_csv(here/'iowa_registered_rectangle_overlap.csv',index=False)
print('registered rectangle intersection/smaller:',ratio,'temporal gap:',0,'days')
