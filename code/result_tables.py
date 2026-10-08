"""Read existing numerical evidence and export transparent result tables."""
from pathlib import Path
import json
import itertools
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# Paths are relative to this repository so a fresh clone rebuilds the released tables.
HERE=Path(__file__).absolute().parent
RELEASE_ROOT=HERE.parent
ROOT=RELEASE_ROOT/'data/upstream'
OUT=RELEASE_ROOT/'data/derived'
V2=ROOT/'analysis_v2'

def main():
    s=pd.read_csv(ROOT/'analysis/results/analysis/opera_dswx_multiscale_v1/historical_hls_sar_summary.csv').query('budget==0.2').set_index('scale_km')
    e=pd.read_csv(ROOT/'analysis/results/analysis/opera_dswx_multiscale_v1/historical_hls_sar_per_event_metrics.csv').query('budget==0.2')
    gate=e.groupby('scale_km').n_cells.apply(lambda z:(z>=20).sum())
    table=s[['event_count','topk_overlap_mean','topk_overlap_ci_low','topk_overlap_ci_high','spearman_mean','spearman_ci_low','spearman_ci_high']].copy()
    table.insert(1,'events_ge20_units',gate)
    table.to_csv(OUT/'results_table3_all5.csv')
    delta=float(s.loc[.5,'topk_overlap_mean']-s.loc[10,'topk_overlap_mean'])
    budget=pd.read_csv(ROOT/'analysis/results/analysis/hls_indices/product_sensitivity/product_budget_curves.csv')
    macro=pd.read_csv(ROOT/'analysis/results/analysis/hls_indices/product_sensitivity/product_macro_curves.csv')
    rows=[]
    for product in ['DSWx','MNDWI','AWEI']:
        for scale in [500,10000]:
            m=macro[macro['product'].eq(product)&macro.domain.eq('product_active')&macro.scale_m.eq(scale)].iloc[0]
            for q in [.1,.2]:
                for min_units in [10,20]:
                    d=budget[budget['product'].eq(product)&budget.scale_m.eq(scale)&budget.budget_fraction.eq(q)&budget.candidate_unit_count.ge(min_units)]
                    rows.append({'product':product,'scale_m':scale,'budget':q,'overlap_min_units':min_units,'rank_event_count':int(m.estimable_event_count),'spearman_mean':m.spearman_macro_mean,'overlap_event_count':len(d),'overlap_mean':d.overlap_coefficient.mean(),'source':'product_budget_curves.csv; rank from original product_macro_curves.csv'})
    a=pd.DataFrame(rows);a.to_csv(OUT/'results_algorithm_10_20_comparison.csv',index=False)
    a[a.budget.eq(.2)&a.overlap_min_units.eq(10)].to_csv(OUT/'results_algorithm_top20.csv',index=False)
    # Export precise mechanistic quantities for both products.
    mech=pd.read_csv(ROOT/'analysis/results/analysis/opera_dswx_mechanisms_v1/spatial_mechanisms_summary.csv')
    cols=['scale_km','s30_rank_persistence_mean','l30_rank_persistence_mean','s30_sd_ratio_mean','l30_sd_ratio_mean']
    mech[cols].to_csv(OUT/'results_mechanism_correct_labels.csv',index=False)
    # Recompute both old 10% and revised 20% Otsu checks on product-active units.
    otsu=[]
    for event in ['C2_2025_LOWER_OHIO','D3_2024_CENTRAL_INDIANA','D5_2024_NEBRASKA_IOWA']:
        for mode,folder in [('fixed',ROOT/'analysis/results/analysis/hls_indices'),('otsu',V2/'results/threshold_sensitivity')]:
            d=pd.read_parquet(folder/'cells'/f'{event}_hls_index_500m_cells.parquet')
            d=d[d.four_chain_strict_qualified.astype(bool)].copy()
            for scale in [500,10000]:
                d['gx']=np.floor(d.x_center_m/scale).astype(int);d['gy']=np.floor(d.y_center_m/scale).astype(int)
                counts=['four_chain_common_pixel_count','mndwi_s30_water_pixel_count','mndwi_l30_water_pixel_count','mndwi_union_pixel_count']
                g=d.groupby(['gx','gy'])[counts].sum().reset_index()
                g=g[g.mndwi_union_pixel_count.gt(0)].copy()
                g['s']=g.mndwi_s30_water_pixel_count/g.four_chain_common_pixel_count
                g['l']=g.mndwi_l30_water_pixel_count/g.four_chain_common_pixel_count
                for q in [.1,.2]:
                    k=int(np.ceil(q*len(g)))
                    # Retain original y then x tie ordering for the Otsu check.
                    sa=set(g.sort_values(['s','gy','gx'],ascending=[False,True,True]).head(k).index)
                    la=set(g.sort_values(['l','gy','gx'],ascending=[False,True,True]).head(k).index)
                    otsu.append({'event_id':event,'threshold_mode':mode,'scale_m':scale,'active_units':len(g),'budget':q,'k':k,'spearman':spearmanr(g.s,g.l).statistic,'overlap':len(sa&la)/k})
    otsu=pd.DataFrame(otsu);otsu.to_csv(OUT/'results_otsu_event_10_20.csv',index=False)
    om=otsu.groupby(['threshold_mode','scale_m','budget'])[['spearman','overlap']].mean().reset_index()
    om.to_csv(OUT/'results_otsu_macro_10_20.csv',index=False)
    original_otsu=pd.read_csv(V2/'results/threshold_sensitivity_metrics.csv')
    oc=otsu[otsu.budget.eq(.1)].merge(original_otsu,on=['event_id','threshold_mode','scale_m'],suffixes=('_new','_old'))
    assert np.allclose(oc.spearman_new,oc.spearman_old,atol=1e-12)
    assert np.allclose(oc.overlap,oc.top10_overlap,atol=1e-12)
    oc.to_csv(OUT/'results_otsu_baseline_reproduction.csv',index=False)
    # County sensitivity example and paired score contrast are evidence, not
    # new independent flood observations.
    sc=pd.read_csv(OUT/'support_sensitivity/county_scores_and_selections.csv')
    sc[sc.event_id.str.contains('SOUTHDAKOTA')].to_csv(OUT/'support_sensitivity/south_dakota_county_score_switch.csv',index=False)
    u=pd.read_csv(OUT/'support_sensitivity/utility_event_metrics.csv')
    from support_sensitivity import ci, flip
    paired=[]
    exact_tests={}
    for threshold,g in u[u.estimable].groupby('threshold'):
        pivot=g.pivot(index='event_id',columns='score',values='lift')
        for comparator in ['s30_water_fraction','l30_water_fraction','consensus_rank']:
            paired_delta=pivot.agreement_weighted_score-pivot[comparator]
            lo,hi=ci(paired_delta)
            values=paired_delta.to_numpy()
            observed=float(values.mean())
            permutations=np.array([(values*np.array(signs)).mean() for signs in itertools.product([-1,1],repeat=len(values))])
            two_sided=float(np.mean(np.abs(permutations)>=abs(observed)-1e-15))
            paired.append({'threshold':threshold,'comparison':'AWC minus '+comparator,'events':len(paired_delta),'mean_lift_difference':observed,'ci95_low':lo,'ci95_high':hi,'exact_sign_flip_p':flip(paired_delta,0),'exact_sign_flip_p_greater':flip(paired_delta,0),'exact_sign_flip_p_two_sided':two_sided})
            exact_tests[f'{threshold}_AWC_minus_{comparator}']={'event_order':pivot.index.tolist(),'difference_vector':values.tolist(),'observed_mean':observed,'one_sided_greater':flip(paired_delta,0),'two_sided_absolute_mean':two_sided,'n_permutations':len(permutations)}
        values=(pivot.agreement_weighted_score-1).to_numpy()
        observed=float(values.mean())
        permutations=np.array([(values*np.array(signs)).mean() for signs in itertools.product([-1,1],repeat=len(values))])
        exact_tests[f'{threshold}_AWC_minus_random']={'event_order':pivot.index.tolist(),'difference_vector':values.tolist(),'observed_mean':observed,'one_sided_greater':flip(values,0),'two_sided_absolute_mean':float(np.mean(np.abs(permutations)>=abs(observed)-1e-15)),'n_permutations':len(permutations)}
    (OUT/'final_sign_flip_verification.json').write_text(json.dumps(exact_tests,indent=2),encoding='utf-8')
    pd.DataFrame(paired).to_csv(OUT/'support_sensitivity/paired_lift_differences.csv',index=False)
    result={'overlap_500m':s.loc[.5,'topk_overlap_mean'],'overlap_10km':s.loc[10,'topk_overlap_mean'],'unrounded_decrease':delta,'decrease_three_decimals':f'{delta:.3f}','all_table3_summaries_use_5_events':bool((s.event_count==5).all()),'table3_ge20_counts':{str(k):int(v) for k,v in gate.items()},'scale_budget_values':sorted(pd.read_csv(ROOT/'analysis/results/analysis/opera_dswx_multiscale_v1/historical_hls_sar_summary.csv').budget.unique().tolist()),'scale_bootstrap_repetitions':5000,'utility_bootstrap_repetitions':10000,'legacy_algorithm_overlap_budget':.1,'algorithm_rank_domain':'product_active','algorithm_legacy_overlap_min_units':10}
    (OUT/'results_numerical_summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2));print(a[a.budget.eq(.2)&a.overlap_min_units.eq(10)].to_string(index=False));print(om.to_string(index=False))

if __name__=='__main__': main()
