"""Exploratory county score sensitivity to fixed-grid block resampling and undefined denominators.

This is an empirical perturbation of observed 500 m cells within each county, not
an inferential spatial confidence interval, external validation or map-accuracy model.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

BASE=Path(__file__).resolve().parent
INPUT=BASE/'inputs'
OUT=BASE/'results'
OUT.mkdir(exist_ok=True)
SEED=20261115
DRAWS=2000
EVENTS=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
FIELDS=['strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count','strict_intersection_pixel_count','strict_union_pixel_count']
county=pd.read_csv(INPUT/'county_scores_and_selections.csv',dtype={'county_fips':str})
ref=county[np.isclose(county.threshold,.95)].copy()
assert len(ref)==37
shapes=json.loads((INPUT/'counties_2025_semigeneral.geojson').read_text(encoding='utf8'))['features']
project=Transformer.from_crs(4326,5070,always_xy=True).transform
states=set(ref.county_fips.str[:2])
pairs=[(str(x['properties']['FIPS']).zfill(5),transform(project,shape(x['geometry']))) for x in shapes if str(x['properties']['FIPS']).zfill(5)[:2] in states]
fips=np.array([p[0] for p in pairs]);tree=shapely.STRtree([p[1] for p in pairs])
def assign(points):
 ix=tree.query(points,predicate='intersects')
 joins=pd.DataFrame({'row':ix[0],'fips':fips[ix[1]]}).sort_values(['row','fips']).drop_duplicates('row')
 return pd.Series(np.arange(len(points))).map(joins.set_index('row').fips).to_numpy()
def weights(x):
 x=np.asarray(x,float); q=.2; target=q*len(x); cut=np.sort(x)[::-1][int(np.ceil(target))-1]
 a=x>cut;t=x==cut;w=a.astype(float);w[t]=(target-a.sum())/t.sum()
 assert np.isclose(w.sum(),target)
 return w
def scores(c):
 n,s,l,i,u=c.T
 return ((s+l)/(2*n))*np.divide(i,u,out=np.zeros_like(i),where=u>0)
def lift(w,y):return float(w@y/y.sum()/.2) if y.sum()>0 else np.nan
rng=np.random.default_rng(SEED)
rows=[]; countyrows=[]; spinkrows=[]; inputpaths=[]
for event in EVENTS:
 path=next((INPUT/'cells').glob('*'+event+'*'));inputpaths.append(path)
 d=pd.read_parquet(path);d=d[d.strict_common_valid_coverage.ge(.95)&d.strict_common_valid_pixel_count.gt(0)].copy().reset_index(drop=True)
 d['county_fips']=assign(shapely.points(d.x_center_m.to_numpy(),d.y_center_m.to_numpy()))
 c=ref[ref.event_id.eq(event)].sort_values('county_fips').copy().reset_index(drop=True)
 d=d[d.county_fips.isin(c.county_fips)].copy()
 grouped=d.groupby('county_fips')[FIELDS].sum().reindex(c.county_fips)
 assert not grouped.isna().any().any()
 assert np.allclose(grouped.to_numpy(),c[FIELDS].to_numpy(),rtol=1e-12,atol=1e-12)
 base_score=scores(grouped.to_numpy(float)); assert np.allclose(base_score,c.agreement_weighted_score,rtol=1e-12,atol=1e-12)
 base_weights=weights(base_score);y=c.rma_indemnity_usd.fillna(0).to_numpy(float)
 for scale in [2500,5000]:
  blocks=[]
  for f in c.county_fips:
   g=d[d.county_fips.eq(f)].copy();g['bx']=np.floor_divide(g.x_index,scale//500);g['by']=np.floor_divide(g.y_index,scale//500)
   blocks.append(g.groupby(['bx','by'])[FIELDS].sum().to_numpy(float))
  nblocks=np.array([len(b) for b in blocks]);samples=np.empty((DRAWS,len(c))); drawweights=np.empty_like(samples); drawlift=np.full(DRAWS,np.nan)
  for j,b in enumerate(blocks):
   # Exactly B blocks selected with replacement within this county; block sums carry all paired cell counts.
   selections=rng.multinomial(len(b),np.full(len(b),1/len(b)),size=DRAWS)
   samples[:,j]=scores(selections @ b)
  for j in range(DRAWS):
   drawweights[j]=weights(samples[j]);drawlift[j]=lift(drawweights[j],y)
  rows.append({'event_id':event,'block_m':scale,'draws':DRAWS,'n_counties':len(c),'blocks_min':int(nblocks.min()),'blocks_max':int(nblocks.max()),'counties_one_block':int((nblocks==1).sum()),'baseline_awc_lift':lift(base_weights,y),'draw_lift_median':float(np.nanmedian(drawlift)) if y.sum()>0 else np.nan,'draw_lift_q025':float(np.nanquantile(drawlift,.025)) if y.sum()>0 else np.nan,'draw_lift_q975':float(np.nanquantile(drawlift,.975)) if y.sum()>0 else np.nan,'selection_vector_unchanged_fraction':float(np.mean(np.all(np.isclose(drawweights,base_weights),axis=1)))})
  for j,r in c.iterrows():
   countyrows.append({'event_id':event,'block_m':scale,'county_fips':r.county_fips,'county_name':r.county_name,'n_blocks':int(nblocks[j]),'baseline_awc':base_score[j],'baseline_selection_weight':base_weights[j],'mean_selection_weight_under_perturbation':float(drawweights[:,j].mean()),'fraction_positive_selection_weight':float((drawweights[:,j]>0).mean())})
  if 'SOUTHDAKOTA' in event:
   sp=c.index[c.county_name.str.contains('Spink',case=False)].tolist();co=c.index[c.county_name.str.contains('Codington',case=False)].tolist()
   assert len(sp)==len(co)==1
   s=sp[0];k=co[0]
   spinkrows.append({'event_id':event,'block_m':scale,'spink_original_score':base_score[s],'codington_original_score':base_score[k],'fraction_spink_greater':float((samples[:,s]>samples[:,k]).mean()),'fraction_equal':float((samples[:,s]==samples[:,k]).mean()),'fraction_codington_greater':float((samples[:,s]<samples[:,k]).mean()),'spink_blocks':int(nblocks[s]),'codington_blocks':int(nblocks[k])})
pd.DataFrame(rows).to_csv(OUT/'exploratory_block_perturbation_event.csv',index=False)
pd.DataFrame(countyrows).to_csv(OUT/'exploratory_block_perturbation_county.csv',index=False)
pd.DataFrame(spinkrows).to_csv(OUT/'exploratory_block_perturbation_spink_codington.csv',index=False)
# Complete-case alternatives change both candidate counts and the exact 20% fractional allocation.
y=pd.read_csv(INPUT/'primary_external_event_county_outcomes_normalized.csv',dtype={'county_fips':str})
cols=['event_id','county_fips','rma_net_planted_quantity','rma_liability_usd','rma_indemnity_per_planted_qty','rma_loss_ratio_agg']
merged=county.merge(y[cols],on=['event_id','county_fips'],how='left',validate='many_to_one',indicator=True)
assert (merged._merge=='both').all()
normrows=[]
for (threshold,event),g in merged.groupby(['threshold','event_id']):
 for denom,outcome in [('rma_net_planted_quantity','rma_indemnity_per_planted_qty'),('rma_liability_usd','rma_loss_ratio_agg')]:
  valid=g[denom].notna() & g[denom].gt(0)
  for rule,h in [('frozen_zero_convention',g),('complete_case_rerank',g[valid])]:
   if len(h)==0: continue
   v=h[outcome].fillna(0).to_numpy(float);w=weights(h.agreement_weighted_score.to_numpy(float))
   normrows.append({'threshold':threshold,'event_id':event,'denominator':denom,'outcome':outcome,'rule':rule,'original_candidates':len(g),'retained_candidates':len(h),'undefined_denominator_count':int((~valid).sum()),'lift':lift(w,v)})
r=pd.DataFrame(normrows);r.to_csv(OUT/'undefined_denominator_complete_case_event.csv',index=False)
r.groupby(['threshold','denominator','rule'],as_index=False).agg(events=('lift','count'),mean_lift=('lift','mean')).to_csv(OUT/'undefined_denominator_complete_case_summary.csv',index=False)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta={'random_seed':SEED,'draws_per_event_per_block_size':DRAWS,'block_sizes_metres':[2500,5000], 'cell_scope':'95% strict common-valid accepted 500 m cells, original semigeneralized county assignments and original fixed candidate counties; exact county sufficient-statistic and AWC reproduction asserted', 'resampling':'within each county, sample its original number of globally anchored 2.5 km or 5 km blocks with replacement, preserving all 500 m cell counts in each block and paired maps; then recompute scores and fractional budget over fixed candidates', 'limits':['post hoc sensitivity to these block sizes and fixed grid origins, not a calibrated probability of true rank, confidence interval, or independent reference','full map units are not a probability sample; event, observation, map-classification errors not modeled','blocks on opposite sides of county boundaries are sampled independently; spatial dependence across blocks and counties remains','one-block counties are constant in this resampling','resampling changes support counts in each draw while preserving fixed candidate counties','complete case changes candidate set and budget; undefined outcomes are missing, not necessarily zero, and selection may be informative'], 'inputs_sha256':{p.name:digest(p) for p in inputpaths+[INPUT/'county_scores_and_selections.csv',INPUT/'counties_2025_semigeneral.geojson',INPUT/'primary_external_event_county_outcomes_normalized.csv']}}
(OUT/'exploratory_block_perturbation_manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
print('Perturbation event results:');print(pd.DataFrame(rows).to_string(index=False));print('\nSpink / Codington:');print(pd.DataFrame(spinkrows).to_string(index=False));print('\nComplete-case comparisons:');print(pd.read_csv(OUT/'undefined_denominator_complete_case_summary.csv').to_string(index=False))
