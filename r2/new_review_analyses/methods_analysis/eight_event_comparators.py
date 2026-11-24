from pathlib import Path
import numpy as np,pandas as pd
here=Path(__file__).resolve().parent
p=here.parents[1]/'inputs/new_review_archives/legacy_eight_event_utility_metrics.csv'
d=pd.read_csv(p);d=d[np.isclose(d.budget_fraction,.2)&d.outcome_estimable]
scores=['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score']
d=d[d.score.isin(scores)]
assert len(d)==32 and d.event_id.nunique()==8
assert (d.groupby('score').event_id.nunique()==8).all()
d[['event_id','score','candidate_count','capture_lift_over_random']].to_csv(here/'eight_event_rma_all_comparators_event.csv',index=False)
d.groupby('score',as_index=False).agg(events=('event_id','nunique'),mean_lift=('capture_lift_over_random','mean'),events_above_one=('capture_lift_over_random',lambda x:int((x>1).sum()))).to_csv(here/'eight_event_rma_all_comparators_summary.csv',index=False)
print(d.groupby('score').capture_lift_over_random.mean().to_string())
