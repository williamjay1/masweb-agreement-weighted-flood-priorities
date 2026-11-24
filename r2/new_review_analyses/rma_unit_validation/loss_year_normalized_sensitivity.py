from pathlib import Path
import pandas as pd,numpy as np,argparse
ap=argparse.ArgumentParser(description="Repeat frozen county ranking outcomes after removing the mismatched loss-year row")
ap.add_argument('--inputs-dir',type=Path,required=True,help='Directory containing archived scores and normalized outcomes')
ap.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
a=ap.parse_args(); O=a.output_dir; O.mkdir(parents=True,exist_ok=True); base=a.inputs_dir
scores=pd.read_csv(base/'county_scores_and_selections.csv',dtype={'county_fips':str});scores=scores[np.isclose(scores.threshold,.95)]
out=pd.read_csv(base/'primary_external_event_county_outcomes_normalized.csv',dtype={'county_fips':str});g=scores.merge(out[['event_id','county_fips','rma_net_planted_quantity','rma_liability_usd','rma_indemnity_usd']],on=['event_id','county_fips'],validate='one_to_one',suffixes=('','_archive'));assert len(g)==37
assert np.allclose(g.rma_indemnity_usd,g.rma_indemnity_usd_archive)
ix=(g.event_id=='N2023_180114_SOUTHDAKOTA')&(g.county_fips=='46115');assert ix.sum()==1
for c in ['rma_indemnity_usd','rma_net_planted_quantity','rma_liability_usd']:assert float(g.loc[ix,c].iloc[0])>0
sc=['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score'];rows=[]
for variant in ['archived','exclude_loss_year_2022_row']:
 z=g.copy()
 if variant!='archived':
  for c,x in [('rma_indemnity_usd',1935),('rma_net_planted_quantity',7.4),('rma_liability_usd',1935)]:z.loc[ix,c]-=x
 for event,d in z.groupby('event_id'):
  I=d.rma_indemnity_usd.to_numpy(float);A=d.rma_net_planted_quantity.to_numpy(float);L=d.rma_liability_usd.to_numpy(float)
  if I.sum()<=0:continue
  for score in sc:
   w=d[score+'_selection_weight'].to_numpy(float);assert np.isclose(w.sum(),.2*len(d))
   for metric,y in [('indemnity',I),('indemnity_per_planted',np.divide(I,A,out=np.zeros_like(I),where=A>0)),('county_indemnity_to_liability',np.divide(I,L,out=np.zeros_like(I),where=L>0))]:
    if y.sum()<=0:continue
    lift=(w@y/y.sum())/.2
    rows.append(dict(variant=variant,event_id=event,score=score,outcome=metric,lift=lift))
d=pd.DataFrame(rows);assert len(d)==2*4*4*3
d.to_csv(O/'loss_year_all_outcomes_event.csv',index=False)
s=d.groupby(['variant','score','outcome'],as_index=False).agg(events=('event_id','size'),mean_lift=('lift','mean'))
s.to_csv(O/'loss_year_all_outcomes_summary.csv',index=False)
for score in ['agreement_weighted_score','s30_water_fraction']:
 print(s[s.score==score].pivot(index='outcome',columns='variant',values='mean_lift').to_string())
