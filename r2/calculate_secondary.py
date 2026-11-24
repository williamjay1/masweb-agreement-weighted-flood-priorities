"""Exploratory R2 reanalysis of frozen event and county sufficient statistics.
No events, observations, or existing results are changed. No inference assumes
independence of the meteorologically related event episodes.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd

base=Path(__file__).resolve().parent
out=base/'results'
inp=base/'inputs/historical_hls_sar_per_event_metrics.csv'
counties=base/'inputs/county_scores_and_selections.csv'
utility=base/'inputs/utility_event_metrics.csv'
out.mkdir(parents=True,exist_ok=True)
events=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
d=pd.read_csv(inp)
d=d[d.event_id.isin(events)].copy()
assert set(d.event_id)==set(events)
assert not d.duplicated(['event_id','scale_km','budget']).any()
d['uniform_random_overlap']=d.k/d.n_cells
d['uniform_adjusted_overlap']=(d.topk_overlap-d.uniform_random_overlap)/(1-d.uniform_random_overlap)
d.to_csv(out/'grid_all_budgets_chance_reference.csv',index=False)
q=d[np.isclose(d.budget,.2)]
a=q[np.isclose(q.scale_km,.5)].set_index('event_id')
b=q[np.isclose(q.scale_km,10)].set_index('event_id')
assert list(a.index.sort_values())==list(b.index.sort_values())
delta=pd.DataFrame({'n_500m':a.n_cells,'k_500m':a.k,'overlap_500m':a.topk_overlap,'rho_500m':a.spearman,
                    'n_10km':b.n_cells,'k_10km':b.k,'overlap_10km':b.topk_overlap,'rho_10km':b.spearman})
delta['delta_overlap']=delta.overlap_10km-delta.overlap_500m
delta['delta_rho']=delta.rho_10km-delta.rho_500m
assert abs(delta.overlap_500m.mean()-.8393784279949925)<1e-10
assert abs(delta.overlap_10km.mean()-.6827380952380953)<1e-10
delta.to_csv(out/'event_changes_500m_10km.csv')
loo=[]
for excluded in delta.index:
    sample=delta.drop(excluded)
    loo.append({'excluded_event':excluded,'mean_delta_overlap':sample.delta_overlap.mean(),
                'mean_delta_rho':sample.delta_rho.mean()})
pd.DataFrame(loo).to_csv(out/'event_change_leave_one_out.csv',index=False)

def weights(score,q):
    score=np.asarray(score,float)
    if not np.isfinite(score).all(): raise ValueError('nonfinite score')
    target=q*len(score)
    threshold=np.sort(score)[::-1][int(np.ceil(target))-1]
    greater=score>threshold
    tied=score==threshold
    w=greater.astype(float)
    w[tied]=(target-greater.sum())/tied.sum()
    assert np.isclose(w.sum(),target)
    return w

c=pd.read_csv(counties,dtype={'county_fips':str})
assert not c.duplicated(['threshold','event_id','county_fips']).any()
old=pd.read_csv(utility)
rows=[]
for (threshold,event),g in c.groupby(['threshold','event_id'],sort=True):
    s=g.s30_water_fraction.to_numpy(float); l=g.l30_water_fraction.to_numpy(float)
    n=g.strict_common_valid_pixel_count.to_numpy(float)
    u=g.strict_union_pixel_count.to_numpy(float); i=g.strict_intersection_pixel_count.to_numpy(float)
    y=g.rma_indemnity_usd.fillna(0).to_numpy(float)
    assert (n>0).all() and (i<=u).all() and (u<=n).all() and (y>=0).all()
    j=np.divide(i,u,out=np.zeros_like(i),where=u>0)
    scores={'s30_water_fraction':s,'l30_water_fraction':l,'consensus_rank':g.consensus_rank.to_numpy(float),
            'agreement_weighted_score':(s+l)/2*j,'mean_burden':(s+l)/2,
            'intersection_burden':i/n,'minimum_fraction':np.minimum(s,l),
            'geometric_mean_fraction':np.sqrt(s*l),'jaccard_alone':j}
    assert np.allclose(scores['agreement_weighted_score'],g.agreement_weighted_score.to_numpy(float),rtol=1e-12,atol=1e-12)
    for budget in [.05,.10,.15,.20,.25,.30,.35,.40,.45,.50]:
        for score_name,score in scores.items():
            w=weights(score,budget)
            cap=float(w@y/y.sum()) if y.sum()>0 else np.nan
            rows.append({'threshold':threshold,'event_id':event,'score':score_name,'budget':budget,
                         'candidate_count':len(g),'loss_total_usd':y.sum(),'capture':cap,'lift':cap/budget,
                         'selection_weight_sum':w.sum()})
r=pd.DataFrame(rows)
ref=old[old.score.isin(['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score'])]
joined=ref.merge(r[np.isclose(r.budget,.2)],on=['threshold','event_id','score'],validate='one_to_one',suffixes=('_prior','_new'))
assert len(joined)==len(ref)
assert np.allclose(joined.lift_prior,joined.lift_new,equal_nan=True,rtol=1e-11,atol=1e-11)
r.to_csv(out/'county_ablations_event_budget.csv',index=False)
summary=r[r.loss_total_usd>0].groupby(['threshold','score','budget'],as_index=False).agg(events=('lift','size'),mean_lift=('lift','mean'),min_lift=('lift','min'),max_lift=('lift','max'))
assert set(summary.events)=={4}
summary.to_csv(out/'county_ablations_summary.csv',index=False)
inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [inp,counties,utility]}
report={'scope':'post hoc descriptive comparison; not independent validation','inputs_sha256':inputs,
        'n_primary_grid_events':len(events),'n_estimable_rma_events':4,'awclift_95_20':float(summary[(summary.threshold==.95)&(summary.score=='agreement_weighted_score')&(summary.budget==.2)].mean_lift.iloc[0]),
        'old_baseline_validation':{'rows':len(joined),'all_lifts_match':True},
        'overlap_reference':'Expected top k overlap k/n assumes independent uniformly sampled k-element sets; chance-adjusted index is descriptive, and is not a tie-aware null model.',
        'limits':['Scores and budgets evaluated post hoc on same outcomes, not a validation of superiority.','Related event episodes undermine independent-event inference.','Zero-union county Jaccard uses existing J=0 convention.','Exposure-only and normalized comparator require separate verified exposure inputs.']}
(out/'secondary_analysis_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('primary event changes:');print(delta.to_string()); print('\n95% support, 20% budget scores:')
print(summary[(summary.threshold==.95)&(summary.budget==.2)].to_string(index=False));print(json.dumps(report,indent=2))
