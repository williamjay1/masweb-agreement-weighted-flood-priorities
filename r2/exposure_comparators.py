"""Exploratory matched county exposure baselines, using existing RMA aggregates."""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
root=Path(__file__).resolve().parent/'results'
root.mkdir(exist_ok=True)
base=Path(__file__).resolve().parent/'inputs'
county=base/'county_scores_and_selections.csv'
outcomes=base/'primary_external_event_county_outcomes_normalized.csv'
blocks=base/'huc8_block_assignments.csv'
c=pd.read_csv(county,dtype={'county_fips':str}); c=c[np.isclose(c.threshold,.95)].copy()
y=pd.read_csv(outcomes,dtype={'county_fips':str})
cols=['event_id','county_fips','rma_indemnity_usd','rma_net_planted_quantity','rma_liability_usd','rma_indemnity_per_planted_qty','rma_loss_ratio_agg']
y=y[cols]
assert not y.duplicated(['event_id','county_fips']).any()
d=c.merge(y,on=['event_id','county_fips'],how='left',validate='one_to_one',suffixes=('','_rebuilt'),indicator=True)
assert (d._merge=='both').all()
assert np.allclose(d.rma_indemnity_usd.fillna(0),d.rma_indemnity_usd_rebuilt.fillna(0),rtol=1e-12,atol=1e-8)
for col in cols[3:]: assert d[col].notna().all() and (d[col]>=0).all()
def weights(score,q=.2):
    score=np.asarray(score,float); target=len(score)*q
    cutoff=np.sort(score)[::-1][int(np.ceil(target))-1]
    above=score>cutoff; ties=score==cutoff
    w=above.astype(float);w[ties]=(target-above.sum())/ties.sum()
    assert np.isclose(w.sum(),target)
    return w
rows=[]
for event,g in d.groupby('event_id'):
    scores={k:g[k].to_numpy(float) for k in ['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score','rma_net_planted_quantity','rma_liability_usd']}
    outcomes_={k:g[k].to_numpy(float) for k in ['rma_indemnity_usd','rma_indemnity_per_planted_qty','rma_loss_ratio_agg']}
    for sk,score in scores.items():
        w=weights(score)
        for yk,values in outcomes_.items():
            capture=float(w@values/values.sum()) if values.sum()>0 else np.nan
            rows.append({'event_id':event,'score':sk,'outcome':yk,'n_counties':len(g),'total_outcome':values.sum(),'capture':capture,'lift':capture/.20})
r=pd.DataFrame(rows);r.to_csv(root/'exposure_comparators_event.csv',index=False)
s=r[np.isfinite(r.lift)].groupby(['score','outcome'],as_index=False).agg(n_events=('lift','size'),mean_lift=('lift','mean'),min_lift=('lift','min'),max_lift=('lift','max'))
s.to_csv(root/'exposure_comparators_summary.csv',index=False)
for outcome,expected in [('rma_indemnity_per_planted_qty',1.160),('rma_loss_ratio_agg',1.073)]:
    actual=s[(s.score=='agreement_weighted_score')&(s.outcome==outcome)].mean_lift.iloc[0]
    assert round(actual,3)==expected,(outcome,actual)
b=pd.read_csv(blocks,dtype={'county_fips':str,'huc8':str})
g=d[['event_id','county_fips']].merge(b,on=['event_id','county_fips'],how='left',validate='one_to_one')
assert g.huc8.notna().all()
counts=g.groupby('event_id').agg(n_counties=('county_fips','size'),n_huc8=('huc8','nunique')).reset_index()
counts.to_csv(root/'huc8_event_block_counts.csv',index=False)
metadata={'input_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [county,outcomes,blocks]},'normalization_note':'zero denominator outcome was set to zero in frozen source; that convention can obscure undefined values; count and report separately','exposure_baseline_note':'exposure values aggregated from event-month RMA records, potentially outcome-associated; retrospective benchmark, not independent or prospective exposure','reproduced_AWC_means_to_three_decimals':{'per_planted':1.160,'county_loss_ratio':1.073}}
(root/'exposure_comparator_manifest.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
print(s.to_string(index=False));print(counts.to_string(index=False))
print('Zero denominators by event',d.groupby('event_id')[['rma_net_planted_quantity','rma_liability_usd']].agg(lambda x: int((x==0).sum())).to_string())
