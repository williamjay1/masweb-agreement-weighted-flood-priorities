from pathlib import Path
import math, json, hashlib
import numpy as np,pandas as pd
from scipy.stats import kendalltau,spearmanr
src=Path(__file__).resolve().parents[2]/'inputs'
old=src/'new_review_archives'
out=Path(__file__).resolve().parent;out.mkdir(parents=True,exist_ok=True)
events=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
p=src/'primary_500m_cells.parquet'
cols=['event_id','x_index','y_index','strict_common_valid_coverage','strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count']
d=pd.read_parquet(p,columns=cols)
d=d[d.event_id.isin(events)&d.strict_common_valid_coverage.ge(.95)&d.strict_common_valid_pixel_count.gt(0)].copy()
assert len(d)==44510
ref=pd.read_csv(src/'historical_hls_sar_per_event_metrics.csv')
ref=ref[ref.event_id.isin(events)&np.isclose(ref.budget,.2)].copy()
rows=[]
for event,g in d.groupby('event_id',sort=True):
 for scale in [.5,1,2,5,10,20,30]:
  factor=int(scale*2);g=g.assign(gx=g.x_index//factor,gy=g.y_index//factor)
  grid=g.groupby(['gx','gy'],as_index=False)[cols[-3:]].sum()
  n=len(grid);den=grid.strict_common_valid_pixel_count.to_numpy(float)
  a=grid.strict_s30_water_pixel_count.to_numpy(float)/den
  b=grid.strict_l30_water_pixel_count.to_numpy(float)/den
  distinct_a=len(np.unique(a));distinct_b=len(np.unique(b))
  rho=float(spearmanr(a,b).statistic) if n>=3 and min(distinct_a,distinct_b)>1 else np.nan
  tau=float(kendalltau(a,b,variant='b').statistic) if n>=3 and min(distinct_a,distinct_b)>1 else np.nan
  k=math.ceil(.2*n)
  order_a=np.lexsort((grid.gy,grid.gx,-a))[:k]; order_b=np.lexsort((grid.gy,grid.gx,-b))[:k]
  overlap=len(set(order_a)&set(order_b))/k
  rows.append({'event_id':event,'scale_km':scale,'n':n,'k':k,'k_over_n':k/n,'overlap':overlap,'spearman':rho,'kendall_tau_b':tau,'distinct_s30':distinct_a,'distinct_l30':distinct_b,'meets_20_unit_rule':n>=20})
x=pd.DataFrame(rows)
j=x.merge(ref,on=['event_id','scale_km'],validate='one_to_one',suffixes=('_recomputed','_frozen'))
assert len(j)==35 and (j.n==j.n_cells).all() and (j.k_recomputed==j.k_frozen).all()
assert np.allclose(j.overlap,j.topk_overlap,rtol=0,atol=1e-12)
j['rho_diff']=j.spearman_recomputed-j.spearman_frozen;j['tau_diff']=j.kendall_tau_b-j.kendall
x.to_csv(out/'primary_all_scales_event_metrics.csv',index=False)
j[['event_id','scale_km','n','k_recomputed','rho_diff','tau_diff']].to_csv(out/'rank_reproduction_differences.csv',index=False)
summary=x.groupby('scale_km',as_index=False).agg(n_events=('n','size'),n_at_least_20=('meets_20_unit_rule','sum'),n_min=('n','min'),n_max=('n','max'),rho_mean=('spearman','mean'),rho_min=('spearman','min'),rho_max=('spearman','max'),tau_mean=('kendall_tau_b','mean'),tau_min=('kendall_tau_b','min'),tau_max=('kendall_tau_b','max'),overlap_mean=('overlap','mean'),overlap_min=('overlap','min'),overlap_max=('overlap','max'))
summary.to_csv(out/'primary_all_scales_descriptive.csv',index=False)
for rule in [20,50,100]:
 keep=x[x.n>=rule]
 keep.groupby('scale_km',as_index=False).agg(n_events=('n','size'),rho_mean=('spearman','mean'),tau_mean=('kendall_tau_b','mean'),overlap_mean=('overlap','mean')).assign(min_units=rule).to_csv(out/f'unit_cutoff_{rule}_sensitivity.csv',index=False)
a=x[x.scale_km==.5].set_index('event_id');b=x[x.scale_km==10].set_index('event_id')
paired=pd.DataFrame({'n_500m':a.n,'overlap_500m':a.overlap,'rho_500m':a.spearman,'tau_b_500m':a.kendall_tau_b,'n_10km':b.n,'overlap_10km':b.overlap,'rho_10km':b.spearman,'tau_b_10km':b.kendall_tau_b})
for col in ['overlap','rho','tau_b']:paired[f'{col}_delta_10km_minus_500m']=paired[f'{col}_10km']-paired[f'{col}_500m']
paired.to_csv(out/'paired_event_differences.csv')
# Preserve the frozen 0.95 support candidate universe and existing selection weights.
scores=pd.read_csv(src/'county_scores_and_selections.csv',dtype={'county_fips':str})
scores=scores[np.isclose(scores.threshold,.95)&scores.event_id.isin(events)]
outcomes=pd.read_csv(src/'primary_external_event_county_outcomes_normalized.csv',dtype={'county_fips':str})
assert not outcomes.duplicated(['event_id','county_fips']).any()
g=scores.merge(outcomes[['event_id','county_fips','noaa_flood_record_count','any_noaa_flood_record','rma_liability_usd','rma_indemnity_usd']],on=['event_id','county_fips'],validate='one_to_one',suffixes=('','_archived'))
assert len(g)==37
y=g.any_noaa_flood_record.fillna(False).astype(bool).astype(int)
assert (y==g.noaa_flood_record_count.fillna(0).gt(0).astype(int)).all()
g['noaa_binary']=y
oldnoaa=pd.read_csv(old/'event_utility_metrics_noaa.csv')
oldnoaa=oldnoaa[oldnoaa.event_id.isin(events)&np.isclose(oldnoaa.budget_fraction,.2)]
assert len(oldnoaa)==20
rr=[]
for event,h in g.groupby('event_id'):
 for score in ['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score']:
  w=h[score+'_selection_weight'].to_numpy(float); y=h.noaa_binary.to_numpy(float)
  cap=float(w@y/y.sum());rr.append(dict(event_id=event,score=score,candidate_count=len(h),flood_count=int(y.sum()),capture=cap,lift=cap/.2))
noaa=pd.DataFrame(rr)
m=noaa.merge(oldnoaa,on=['event_id','score'],validate='one_to_one')
assert np.allclose(m.lift,m.capture_lift_over_random,rtol=0,atol=1e-12)
noaa.to_csv(out/'noaa_binary_comparators_event.csv',index=False)
noaa.groupby('score',as_index=False).agg(events=('event_id','count'),mean_capture=('capture','mean'),mean_lift=('lift','mean'),min_lift=('lift','min'),max_lift=('lift','max')).to_csv(out/'noaa_binary_comparators_summary.csv',index=False)
# Diagnose the actual archived HUC8 draws, including undefined event draws.
draws=pd.read_csv(old/'huc8_block_bootstrap_draws.csv')
rr=[]
for (score,outcome),h in draws.groupby(['score','outcome']):
 piv=h.pivot(index='draw',columns='event_id',values='capture_lift_over_random')
 counts=piv.notna().sum(axis=1)
 means=piv.mean(axis=1)
 rr.append({'score':score,'outcome':outcome,'draws':len(piv),'events_all_defined':int((counts==4).sum()),'events_less_than_four':int((counts<4).sum()),'min_defined_events':int(counts.min()),'max_defined_events':int(counts.max()),'mean_legacy_draw_mean':means.mean(),'q025_legacy':means.quantile(.025),'q975_legacy':means.quantile(.975)})
pd.DataFrame(rr).to_csv(out/'huc8_actual_draw_diagnostics.csv',index=False)
digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
report={'cells_sha256':digest(p),'frozen_metrics_sha256':digest(src/'historical_hls_sar_per_event_metrics.csv'),'event_scales':len(j),'max_abs_spearman_difference':float(j.rho_diff.abs().max()),'max_abs_kendall_difference':float(j.tau_diff.abs().max()),'all_n_and_topk_match':True,'noaa_baseline_event_score_rows_all_match':len(m),'huc8_source':'inputs/new_review_archives/huc8_block_bootstrap_draws.csv','interpretation':'5 events; event ranges are descriptive and do not establish independent-event uncertainty. Minimum-unit sensitivity is post hoc. NOAA and event selection share administrative source.'}
(out/'analysis_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2));print(summary.to_string(index=False));print(noaa.groupby('score').lift.agg(['mean','min','max']).to_string());print(pd.DataFrame(rr).to_string(index=False))

