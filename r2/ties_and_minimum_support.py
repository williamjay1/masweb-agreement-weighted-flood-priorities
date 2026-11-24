"""Expected independent random tie resolutions and exploratory support filters.

Outputs remain post-hoc sensitivity analyses, not a new prespecified primary.
"""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
from scipy.stats import spearmanr
out=Path(__file__).resolve().parent/'results'
out.mkdir(exist_ok=True)
source=Path(__file__).resolve().parent/'inputs/primary_500m_cells.parquet'
frozen=Path(__file__).resolve().parent/'inputs/historical_hls_sar_per_event_metrics.csv'
events=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
fields=['eligible_pixel_count','strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count']
data=pd.read_parquet(source,columns=['event_id','x_index','y_index','strict_common_valid_coverage']+fields)
data=data[data.event_id.isin(events)&data.strict_common_valid_coverage.ge(.95)&data.strict_common_valid_pixel_count.gt(0)]
assert len(data)==44510
def select_prob(v,k):
    threshold=np.partition(v,len(v)-k)[len(v)-k]
    above=v>threshold; ties=v==threshold
    p=above.astype(float);p[ties]=(k-above.sum())/ties.sum()
    assert np.isclose(p.sum(),k)
    return p,int(ties.sum()),float(threshold)
rows=[]
for minimum in [1,10,25,50]:
    for event,group in data.groupby('event_id'):
        group=group[group.eligible_pixel_count>=minimum].copy()
        for scale in [.5,1,2,5,10,20,30]:
            group['gx']=group.x_index//int(scale*2);group['gy']=group.y_index//int(scale*2)
            grid=group.groupby(['gx','gy'],sort=True,as_index=False)[fields].sum()
            n=len(grid)
            if n<2:continue
            s=grid.strict_s30_water_pixel_count.to_numpy(float)/grid.strict_common_valid_pixel_count.to_numpy(float)
            l=grid.strict_l30_water_pixel_count.to_numpy(float)/grid.strict_common_valid_pixel_count.to_numpy(float)
            rho=float(spearmanr(s,l).statistic) if np.unique(s).size>1 and np.unique(l).size>1 else np.nan
            for q in [.05,.1,.2,.3,.4,.5]:
                k=int(np.ceil(q*n))
                ps,ns,ts=select_prob(s,k);pl,nl,tl=select_prob(l,k)
                aa=set(grid.assign(v=s).sort_values(['v','gx','gy'],ascending=[False,True,True]).head(k).index)
                bb=set(grid.assign(v=l).sort_values(['v','gx','gy'],ascending=[False,True,True]).head(k).index)
                deterministic=len(aa&bb)/k
                expected=float(ps@pl/k)
                rows.append({'minimum_eligible_pixels':minimum,'event_id':event,'scale_km':scale,'budget':q,
                             'accepted_500m_cells':len(group),'units':n,'k':k,'rho':rho,
                             'overlap_coordinate':deterministic,'overlap_expected_independent_random_ties':expected,
                             's_cutoff_tie_size':ns,'l_cutoff_tie_size':nl,'s_cutoff':ts,'l_cutoff':tl,
                             'uniform_random_overlap_k_over_n':k/n})
r=pd.DataFrame(rows)
old=pd.read_csv(frozen);old=old[old.event_id.isin(events)]
check=r[r.minimum_eligible_pixels.eq(1)].merge(old,on=['event_id','scale_km','budget'],validate='one_to_one')
assert len(check)==len(old)==210
assert np.all(check.units==check.n_cells)
assert np.allclose(check.overlap_coordinate,check.topk_overlap,atol=1e-12,rtol=0)
check['rho_recomputed_minus_frozen']=check.rho-check.spearman
check[['event_id','scale_km','budget','rho','spearman','rho_recomputed_minus_frozen']].to_csv(out/'tie_sensitivity_rho_reproduction_differences.csv',index=False)
print('Max absolute rho difference:',check.rho_recomputed_minus_frozen.abs().max())
r.to_csv(out/'tie_and_support_sensitivity.csv',index=False)
summary=r[np.isclose(r.budget,.2)&r.scale_km.isin([.5,10])].groupby(['minimum_eligible_pixels','scale_km'],as_index=False).agg(events=('event_id','size'),n_spearman_defined=('rho','count'),mean_overlap_coordinate=('overlap_coordinate','mean'),mean_overlap_random_tie=('overlap_expected_independent_random_ties','mean'),mean_spearman=('rho','mean'),sum_base_cells=('accepted_500m_cells','sum'))
summary.to_csv(out/'tie_and_support_sensitivity_summary.csv',index=False)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
metadata={'source_sha256':digest(source),'frozen_event_metrics_sha256':digest(frozen),'baseline_rows':len(check),'baseline_coordinate_overlap_all_agree':True,'max_absolute_rho_difference':float(check.rho_recomputed_minus_frozen.abs().max()),
          'interpretation':'Analytical expected overlap under independent random selection within each sensor cutoff tie set; not randomizing the shared scores or an empirical null of independence. Minimum support filters are post hoc, not prespecified and alter the analysis population.',
          'warning':'Expected overlaps are fractional expected counts; no stochastic Monte Carlo or uncertainty intervals were computed.'}
(out/'tie_and_support_manifest.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print(summary.to_string(index=False)); print('\nWisconsin 500m top20:');print(r[(r.minimum_eligible_pixels==1)&(r.event_id.str.contains('WISCONSIN'))&(r.scale_km==.5)&(r.budget==.2)].to_string(index=False)); print(json.dumps(metadata,indent=2))
