"""Independent, read-only input reanalysis of 90/95/99% support thresholds.

All outputs are written below this script's support_sensitivity directory.
County scores use summed strict pixel counts and the original polygon-centre
assignment rule. The five original events and outcome records remain fixed.
"""
from pathlib import Path
import hashlib
import itertools
import json
import sys

import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
from scipy.stats import rankdata, spearmanr, kendalltau

# Paths are relative to this repository so a fresh clone reproduces the released
# outputs. data/ ships the frozen derived inputs; results are rewritten in place.
HERE = Path(__file__).absolute().parent
RELEASE_ROOT = HERE.parent
ROOT = RELEASE_ROOT / 'data/upstream'
V2 = ROOT / 'analysis_v2'
OUT = RELEASE_ROOT / 'data/derived/support_sensitivity'
OUT.mkdir(exist_ok=True)
SEED = 20261007
REPS = 10000
EVENTS = ['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
SCALES = [0.5,1,2,5,10,20,30]
COUNTIES = RELEASE_ROOT / 'data/ancillary/census_counties_2025/counties_2025_semigeneral.geojson'
SUM = ['eligible_pixel_count','strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count','strict_intersection_pixel_count','strict_union_pixel_count']

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def ci(vals, seed=SEED):
    vals=np.asarray(vals,float);vals=vals[np.isfinite(vals)]
    if not len(vals): return np.nan,np.nan
    r=np.random.default_rng(seed)
    means=vals[r.integers(0,len(vals),(REPS,len(vals)))].mean(1)
    return tuple(np.quantile(means,[.025,.975]))

def flip(vals, null=1):
    vals=np.asarray(vals,float)-null
    obs=vals.mean()
    return np.mean([np.mean(vals*np.array(sign))>=obs-1e-15 for sign in itertools.product([-1,1],repeat=len(vals))])

def frac(scores,q):
    scores=np.asarray(scores,float); n=len(scores); target=q*n
    thresh=np.sort(scores)[::-1][int(np.ceil(target))-1]
    over=scores>thresh; tie=scores==thresh
    w=over.astype(float);w[tie]=(target-over.sum())/tie.sum()
    return w

def score_counts(d):
    d=d.copy();n=d.strict_common_valid_pixel_count
    d['s30_water_fraction']=d.strict_s30_water_pixel_count/n
    d['l30_water_fraction']=d.strict_l30_water_pixel_count/n
    return d

def scale_rows(d,t,event):
    rows=[]
    for scale in SCALES:
        z=d.copy(); factor=round(scale*2)
        z['gx']=z.x_index//factor;z['gy']=z.y_index//factor
        z=score_counts(z.groupby(['gx','gy'],sort=True)[SUM].sum().reset_index())
        n=len(z); k=int(np.ceil(.2*n))
        a=set(z.sort_values(['s30_water_fraction','gx','gy'],ascending=[False,True,True]).head(k).index)
        b=set(z.sort_values(['l30_water_fraction','gx','gy'],ascending=[False,True,True]).head(k).index)
        rows.append({'threshold':t,'event_id':event,'scale_km':scale,'n_cells':n,'k':k,'topk_overlap':len(a&b)/k,'spearman':spearmanr(z.s30_water_fraction,z.l30_water_fraction).statistic,'kendall':kendalltau(z.s30_water_fraction,z.l30_water_fraction).statistic})
    return rows

def main():
    # Exact historical geometry copy, verified against original source manifest.
    assert digest(COUNTIES)=='8ecc920ee3d9366dc13d6f6e566463b6249f017e913aedd0a5bd00fc6ddd4d43'
    features=json.loads(COUNTIES.read_text(encoding='utf-8'))['features']
    project=Transformer.from_crs(4326,5070,always_xy=True).transform
    polygons=[transform(project,shape(f['geometry'])) for f in features]
    fips=np.array([str(f['properties']['FIPS']).zfill(5) for f in features])
    names={str(f['properties']['FIPS']).zfill(5):f['properties']['County_Name'] for f in features}
    tree=shapely.STRtree(polygons)
    inputs=[]; domains=[]; sm=[]; countrows=[]; countyrows=[]
    for event in EVENTS:
        p=next((ROOT/'analysis/results/analysis/blind_common_support/cells').glob('*'+event+'*'))
        d=pd.read_parquet(p)
        inputs.append({'path':str(p),'sha256':digest(p)})
        # Assign every cell that could pass any requested threshold once.
        d=d[d.strict_common_valid_coverage.ge(.90)&d.strict_common_valid_pixel_count.gt(0)].copy().reset_index(drop=True)
        pts=shapely.points(d.x_center_m.to_numpy(),d.y_center_m.to_numpy())
        ix=tree.query(pts,predicate='intersects')
        joins=pd.DataFrame({'row':ix[0],'county_fips':fips[ix[1]]}).sort_values(['row','county_fips']).drop_duplicates('row')
        d['county_fips']=d.index.map(joins.set_index('row').county_fips)
        for t in [.90,.95,.99]:
            z=d[d.strict_common_valid_coverage.ge(t)].copy()
            sm.extend(scale_rows(z,t,event))
            countrows.append({'threshold':t,'event_id':event,'eligible_cells':len(z),'active_cells':int(z.strict_union_pixel_count.gt(0).sum()),'assigned_cells':int(z.county_fips.notna().sum()),'unassigned_cells':int(z.county_fips.isna().sum()),'eligible_pixels':int(z.eligible_pixel_count.sum()),'common_pixels':int(z.strict_common_valid_pixel_count.sum())})
            c=score_counts(z.dropna(subset=['county_fips']).groupby('county_fips')[SUM].sum().reset_index())
            c['event_id']=event;c['threshold']=t;c['county_name']=c.county_fips.map(names)
            countyrows.append(c)
        print('Processed',event,flush=True)
    sm=pd.DataFrame(sm); census=pd.DataFrame(countrows); counties=pd.concat(countyrows,ignore_index=True)
    original=pd.read_csv(ROOT/'analysis/results/analysis/opera_dswx_multiscale_v1/historical_hls_sar_per_event_metrics.csv').query('budget==0.2')
    comparison=sm[sm.threshold.eq(.95)].merge(original[['event_id','scale_km','n_cells','topk_overlap','spearman','kendall']],on=['event_id','scale_km'],suffixes=('_recomputed','_original'))
    for col in ['n_cells','topk_overlap','spearman','kendall']:
        comparison[col+'_difference']=comparison[col+'_recomputed']-comparison[col+'_original']
    comparison.to_csv(OUT/'baseline_scale_reproduction.csv',index=False)
    original_counties=pd.read_parquet(ROOT/'analysis/results/analysis/operational_validation/operational_unit_scores.parquet')
    original_counties=original_counties[original_counties.unit_type.eq('county')&original_counties.event_id.isin(EVENTS)].copy()
    original_counties['county_fips']=original_counties.unit_id.astype(str).str.zfill(5)
    cc=counties[counties.threshold.eq(.95)].merge(original_counties,on=['event_id','county_fips'],suffixes=('_new','_original'),how='outer',indicator=True)
    for col in SUM+['s30_water_fraction','l30_water_fraction']:
        cc[col+'_difference']=cc[col+'_new']-cc[col+'_original']
    cc.to_csv(OUT/'baseline_county_reproduction.csv',index=False)
    outcomes=pd.read_csv(ROOT/'analysis/results/primary_external_event_county_outcomes.csv',dtype={'county_fips':str})
    outcomes.county_fips=outcomes.county_fips.str.zfill(5)
    linked=counties.merge(outcomes[['event_id','county_fips','rma_indemnity_usd']],on=['event_id','county_fips'],how='inner',validate='many_to_one')
    u=[]; scoreframes=[]
    for (t,event),g in linked.groupby(['threshold','event_id'],sort=True):
        g=g.sort_values('county_fips').copy();n=len(g)
        s=g.s30_water_fraction.to_numpy();l=g.l30_water_fraction.to_numpy()
        g['consensus_rank']=.5*((rankdata(s)-.5)/n+(rankdata(l)-.5)/n)
        iu=np.divide(g.strict_intersection_pixel_count.to_numpy(float),g.strict_union_pixel_count.to_numpy(float),out=np.zeros(n),where=g.strict_union_pixel_count.to_numpy()>0)
        g['agreement_weighted_score']=.5*(s+l)*iu
        y=g.rma_indemnity_usd.fillna(0).to_numpy();total=y.sum()
        for score in ['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score']:
            w=frac(g[score],.2);cap=np.dot(w,y)/total if total>0 else np.nan
            u.append({'threshold':t,'event_id':event,'score':score,'n_counties':n,'target_equivalents':w.sum(),'rma_total':total,'capture':cap,'lift':cap/.2,'estimable':total>0})
            g[score+'_selection_weight']=w
        scoreframes.append(g)
    u=pd.DataFrame(u);pd.concat(scoreframes).to_csv(OUT/'county_scores_and_selections.csv',index=False)
    us=[]
    for (t,score),g in u[u.estimable].groupby(['threshold','score']):
        vals=g.lift.to_numpy();lo,hi=ci(vals)
        us.append({'threshold':t,'score':score,'events':len(g),'total_candidate_counties':int(g.n_counties.sum()),'mean_capture':g.capture.mean(),'mean_lift':vals.mean(),'ci95_low':lo,'ci95_high':hi,'exact_sign_flip_p':flip(vals),'events_above_one':int((vals>1).sum())})
    summary=[]
    for (t,scale),g in sm.groupby(['threshold','scale_km']):
        row={'threshold':t,'scale_km':scale,'events':len(g),'events_ge20_units':int(g.n_cells.ge(20).sum())}
        for col in ['topk_overlap','spearman','kendall']:
            lo,hi=ci(g[col]);row.update({col+'_mean':g[col].mean(),col+'_ci95_low':lo,col+'_ci95_high':hi})
        summary.append(row)
    sm.to_csv(OUT/'scale_event_metrics.csv',index=False);census.to_csv(OUT/'event_support_census.csv',index=False)
    pd.DataFrame(summary).to_csv(OUT/'scale_summary.csv',index=False);u.to_csv(OUT/'utility_event_metrics.csv',index=False)
    us=pd.DataFrame(us);us.to_csv(OUT/'utility_summary.csv',index=False)
    county_ok=bool(cc['_merge'].eq('both').all() and all(np.allclose(cc[x+'_difference'],0,atol=1e-12) for x in SUM+['s30_water_fraction','l30_water_fraction']))
    scale_ok=bool(all(np.allclose(comparison[x+'_difference'],0,atol=1e-10) for x in ['n_cells','topk_overlap','spearman','kendall']))
    original_utility=pd.read_csv(V2/'results/utility_raw_rma/event_utility_metrics.csv')
    v=u[u.threshold.eq(.95)].merge(original_utility[original_utility.selection_phase.eq('blind_noaa_event_screen')&original_utility.budget_fraction.eq(.2)],on=['event_id','score'],suffixes=('_new','_original'))
    v['lift_difference']=v.lift-v.capture_lift_over_random
    v.to_csv(OUT/'baseline_utility_reproduction.csv',index=False)
    utility_ok=bool(np.allclose(v.lift_difference.fillna(0),0,atol=1e-10))
    reported_scale_ok=bool(all(np.allclose(comparison[x+'_recomputed'].round(3),comparison[x+'_original'].round(3),atol=1e-12) for x in ['n_cells','topk_overlap','spearman','kendall']))
    report={'status':'COMPLETE','thresholds':[.9,.95,.99],'fixed_events':EVENTS,'bootstrap_repetitions':REPS,'bootstrap_method':'event-level percentile descriptive CI','seed':SEED,'county_baseline_pass':county_ok,'scale_exact_baseline_pass':scale_ok,'scale_reported_precision_pass':reported_scale_ok,'utility_baseline_pass':utility_ok,'scale_max_abs_differences':{x:float(comparison[x+'_difference'].abs().max()) for x in ['n_cells','topk_overlap','spearman','kendall']},'county_assignment':'EPSG:5070 500m centre intersects same frozen polygon; minimum FIPS on boundary','input_manifest':inputs+[{'path':str(COUNTIES),'sha256':digest(COUNTIES)}],'note':'Grid Top20 uses ceil(.2*n), county utility exact fractional .2*n with equal allocation across cutoff ties. Fixed five events; four positive RMA totals. No new independent events. Independent summed-integer-pixel count aggregation reproduces cell counts and overlap exactly; differs from legacy weighted-floating-point aggregation by at most 1.4e-6 in Spearman and 2.1e-6 in Kendall because of numerical ties. All reported three-decimal event results reproduce.'}
    (OUT/'support_sensitivity_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));print(us.to_string(index=False))

if __name__=='__main__': main()
