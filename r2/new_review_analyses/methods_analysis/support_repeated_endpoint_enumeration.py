from pathlib import Path
import itertools
import numpy as np
import pandas as pd
here=Path(__file__).resolve().parent
p=here.parents[1]/'inputs/utility_event_metrics.csv'
d=pd.read_csv(p)
d=d[(d.score=='agreement_weighted_score') & d.estimable & d.threshold.isin([0.9,0.99])]
a=d[d.threshold==0.9].sort_values('event_id');b=d[d.threshold==0.99].sort_values('event_id')
assert len(a)==len(b)==4
assert np.array_equal(a.event_id.to_numpy(),b.event_id.to_numpy())
assert np.array_equal(a.lift.to_numpy(),b.lift.to_numpy())
values=a.lift.to_numpy();draws=np.array([np.mean(x) for x in itertools.product(values,repeat=4)])
q=np.quantile(draws,[0.025,0.975])
pd.DataFrame([{'thresholds':'90% and 99%','events':4,'ordered_event_resamples':len(draws),'percentile_2_5':q[0],'percentile_97_5':q[1]}]).to_csv(here/'support_repeated_endpoint_enumeration.csv',index=False)
print('Identical events and lift at 90% and 99%; 4^4 exact ordered resamples:',q)

full=pd.read_csv(p)
rows=[]
for score in ['s30_water_fraction','l30_water_fraction','consensus_rank']:
    x=full[(full.threshold==.95)&full.estimable&(full.score==score)].capture.to_numpy()
    assert len(x)==4
    q=np.quantile([np.mean(z) for z in itertools.product(x,repeat=4)],.025)
    assert abs(q-.1641555253)<1e-10
    rows.append({'score':score,'events':4,'ordered_event_resamples':256,'percentile_2_5':q})
pd.DataFrame(rows).to_csv(here/'capture_repeated_endpoint_enumeration.csv',index=False)
print('Three comparator capture lower quantiles:', rows)
