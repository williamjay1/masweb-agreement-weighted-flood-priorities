from pathlib import Path
import numpy as np,pandas as pd,json,hashlib
src=Path(__file__).resolve().parents[2]/'inputs';out=Path(__file__).resolve().parent
events=['N2023_179508_MINNESOTA','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
scores=pd.read_csv(src/'county_scores_and_selections.csv',dtype={'county_fips':str})
scores=scores[np.isclose(scores.threshold,.95)&scores.event_id.isin(events)]
outcomes=pd.read_csv(src/'primary_external_event_county_outcomes_normalized.csv',dtype={'county_fips':str})
assignment=pd.read_csv(src/'huc8_block_assignments.csv',dtype={'county_fips':str,'huc8':str})
d=scores.merge(outcomes[['event_id','county_fips','rma_liability_usd','rma_indemnity_usd']],on=['event_id','county_fips'],suffixes=('','_check'),validate='one_to_one')
assert np.allclose(d.rma_indemnity_usd.fillna(0),d.rma_indemnity_usd_check.fillna(0))
d=d.merge(assignment,on=['event_id','county_fips'],validate='one_to_one')
assert len(d)==34
valid=d.rma_liability_usd.notna()&d.rma_liability_usd.gt(0)
excluded=d[~valid].copy();d=d[valid].copy()
excluded[['event_id','county_fips','rma_liability_usd']].to_csv(out/'huc8_liability_excluded_counties.csv',index=False)
assert len(excluded)==5 and len(d)==29 and set(excluded.event_id)=={'N2025_202615_MISSOURI'}
def weights(x,q=.2):
 x=np.asarray(x,float); k=q*len(x);cut=np.sort(x)[::-1][int(np.ceil(k))-1]
 above=x>cut; tie=x==cut;w=above.astype(float);w[tie]=(k-above.sum())/tie.sum();return w
def compute(g,score):
 w=weights(g[score].to_numpy());y=g.rma_indemnity_usd.to_numpy(float);L=g.rma_liability_usd.to_numpy(float)
 total_y=y.sum();selected_y=w@y;total_L=L.sum();selected_L=w@L
 return (selected_y/selected_L)/(total_y/total_L) if total_y>0 and selected_L>0 and total_L>0 else np.nan
sn=['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score']
rng=np.random.default_rng(20261115); reps=2000;rows=[];baseline=[]
for event,g in d.groupby('event_id',sort=True):
 g=g.sort_values('county_fips');blocks=sorted(g.huc8.unique())
 for score in sn:
  baseline.append({'event_id':event,'score':score,'counties':len(g),'huc8_blocks':len(blocks),'all_county_indemnity':g.rma_indemnity_usd.sum(),'all_county_liability':g.rma_liability_usd.sum(),'selected_to_all_aggregate_loss_rate':compute(g,score)})
 for draw in range(reps):
  drawn=rng.choice(blocks,size=len(blocks),replace=True)
  z=pd.concat([g[g.huc8.eq(block)] for block in drawn],ignore_index=True)
  for score in sn:
   rows.append({'event_id':event,'score':score,'draw':draw,'sampled_blocks':len(blocks),'pseudo_county_rows':len(z),'selected_to_all_aggregate_loss_rate':compute(z,score)})
pd.DataFrame(baseline).to_csv(out/'aggregate_liability_rate_baseline_event.csv',index=False)
draws=pd.DataFrame(rows);draws.to_csv(out/'aggregate_liability_rate_block_draws.csv',index=False)
details=[];res=[]
for score,h in draws.groupby('score'):
 pivot=h.pivot(index='draw',columns='event_id',values='selected_to_all_aggregate_loss_rate')
 full=pivot[pivot.notna().all(axis=1)].mean(axis=1)
 baseline_value=np.mean([v['selected_to_all_aggregate_loss_rate'] for v in baseline if v['score']==score])
 res.append({'score':score,'draws':len(pivot),'all_four_estimable':len(full),'at_least_one_undefined':len(pivot)-len(full),'baseline_4event_mean_rate_ratio':baseline_value,'block_draw_mean':full.mean(),'q025_descriptive':full.quantile(.025),'q975_descriptive':full.quantile(.975)})
 for event, col in pivot.items():details.append({'score':score,'event_id':event,'draws':len(col),'undefined_draws':int(col.isna().sum()),'min':col.min(),'median':col.median(),'max':col.max()})
pd.DataFrame(res).to_csv(out/'aggregate_liability_rate_block_summary.csv',index=False)
pd.DataFrame(details).to_csv(out/'aggregate_liability_rate_undefined_event.csv',index=False)
metadata={'seed':20261115,'draws_per_event':reps,'preprocessing':'exclude counties with missing or nonpositive liability before drawing blocks and determining qn; keep prespecified frozen score values','allocation':'fractional top 20 percent of pseudo county rows with ties split; sampled blocks repeat all their county rows','metric':'(sum allocation_weight*county_indemnity / sum allocation_weight*county_liability) / (sum county_indemnity / sum county_liability)','inference':'post hoc within-event block perturbation; not independent events, not ground truth, not proof of superiority. Mean and range only across draws with all four events defined','inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [src/'county_scores_and_selections.csv',src/'primary_external_event_county_outcomes_normalized.csv',src/'huc8_block_assignments.csv']}}
(out/'aggregate_liability_rate_manifest.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
print(pd.DataFrame(baseline).to_string(index=False));print(pd.DataFrame(res).to_string(index=False));print(pd.DataFrame(details).to_string(index=False))

