"""Post hoc 2025 Census TIGER county reassignment, fixed existing event domain."""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import hashlib,json,os
import numpy as np,pandas as pd,shapefile,shapely
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
from scipy.stats import rankdata

base=Path(__file__).resolve().parent
out=base/'results'
out.mkdir(exist_ok=True)
original=base/'inputs/counties_2025_semigeneral.geojson'
archive=Path(os.environ['CENSUS_COUNTY_ZIP'])
frozen=base/'inputs/county_scores_and_selections.csv'
events=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
fields=['eligible_pixel_count','strict_common_valid_pixel_count','strict_s30_water_pixel_count','strict_l30_water_pixel_count','strict_intersection_pixel_count','strict_union_pixel_count']
ref=pd.read_csv(frozen,dtype={'county_fips':str}).query('threshold == 0.95').copy()
states=set(ref.county_fips.str[:2]); project=Transformer.from_crs(4326,5070,always_xy=True).transform
old=json.loads(original.read_text(encoding='utf8'))['features']
oldpairs=[(str(x['properties']['FIPS']).zfill(5),transform(project,shape(x['geometry']))) for x in old if str(x['properties']['FIPS']).zfill(5)[:2] in states]
with ZipFile(archive) as z:
    rd=shapefile.Reader(shp=BytesIO(z.read('tl_2025_us_county.shp')),shx=BytesIO(z.read('tl_2025_us_county.shx')),dbf=BytesIO(z.read('tl_2025_us_county.dbf')),encoding='utf8')
    newpairs=[]
    for sr in rd.iterShapeRecords():
        r=sr.record.as_dict()
        if r['STATEFP'] in states:
            newpairs.append((r['GEOID'],transform(project,shape(sr.shape.__geo_interface__))))
assert len(set(k for k,_ in newpairs))==len(newpairs)
def assign(points,pairs):
    fips=np.asarray([p[0] for p in pairs]); tree=shapely.STRtree([p[1] for p in pairs]);ix=tree.query(points,predicate='intersects')
    joins=pd.DataFrame({'row':ix[0],'fips':fips[ix[1]]}).sort_values(['row','fips']).drop_duplicates('row')
    return pd.Series(np.arange(len(points))).map(joins.set_index('row').fips).to_numpy()
def frac(score):
    n=len(score); target=.2*n; cutoff=np.sort(score)[::-1][int(np.ceil(target))-1]; above=score>cutoff; ties=score==cutoff
    w=above.astype(float);w[ties]=(target-above.sum())/ties.sum();return w
assignments=[]; scores=[]; metrics=[]
for event in events:
    path=next((base/'inputs/cells').glob('*'+event+'*'))
    d=pd.read_parquet(path);d=d[d.strict_common_valid_coverage.ge(.95)&d.strict_common_valid_pixel_count.gt(0)].copy().reset_index(drop=True)
    points=shapely.points(d.x_center_m.to_numpy(),d.y_center_m.to_numpy());d['old_fips']=assign(points,oldpairs);d['official_fips']=assign(points,newpairs)
    candidate=ref[ref.event_id.eq(event)].copy(); candidates=set(candidate.county_fips)
    for label,col in [('original','old_fips'),('census_2025_tiger','official_fips')]:
        tmp=d[d[col].isin(candidates)].groupby(col)[fields].sum().rename_axis('county_fips').reset_index()
        g=candidate[['county_fips','rma_indemnity_usd']].merge(tmp,on='county_fips',how='left',validate='one_to_one')
        if g.strict_common_valid_pixel_count.isna().any() or g.strict_common_valid_pixel_count.le(0).any():raise ValueError((event,label,'candidate lacks common-support cells'))
        n=g.strict_common_valid_pixel_count.to_numpy(float);s=g.strict_s30_water_pixel_count.to_numpy(float)/n;l=g.strict_l30_water_pixel_count.to_numpy(float)/n
        j=np.divide(g.strict_intersection_pixel_count,g.strict_union_pixel_count,out=np.zeros(len(g)),where=g.strict_union_pixel_count.to_numpy()>0)
        g['s30_water_fraction']=s;g['l30_water_fraction']=l;g['consensus_rank']=.5*((rankdata(s)-.5)/len(g)+(rankdata(l)-.5)/len(g));g['agreement_weighted_score']=(s+l)/2*j
        g['event_id']=event;g['boundary']=label;scores.append(g)
        y=g.rma_indemnity_usd.fillna(0).to_numpy(float)
        for score in ['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score']:
            lift=float(frac(g[score].to_numpy())@y/y.sum()/.2) if y.sum()>0 else np.nan
            metrics.append({'event_id':event,'boundary':label,'score':score,'n_counties':len(g),'rma_total':y.sum(),'lift':lift})
    assignments.append({'event_id':event,'cells':len(d),'original_unassigned':int(d.old_fips.isna().sum()),'official_unassigned':int(d.official_fips.isna().sum()),'changed_all_cells':int((d.old_fips.fillna('')!=d.official_fips.fillna('')).sum()),'official_outside_fixed_candidates':int((~d.official_fips.isin(candidates)).sum()),'original_outside_fixed_candidates':int((~d.old_fips.isin(candidates)).sum())})
scores=pd.concat(scores); metrics=pd.DataFrame(metrics);assignments=pd.DataFrame(assignments)
orig=scores[scores.boundary.eq('original')].merge(ref,on=['event_id','county_fips'],suffixes=('_new','_prior'),validate='one_to_one')
for col in fields+['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score']:
    assert np.allclose(orig[col+'_new'],orig[col+'_prior'],atol=1e-12,rtol=1e-12),col
scores.to_csv(out/'census_boundary_county_scores.csv',index=False);metrics.to_csv(out/'census_boundary_event_lifts.csv',index=False);assignments.to_csv(out/'census_boundary_cell_reassignment.csv',index=False)
summary=metrics.groupby(['boundary','score'],as_index=False).agg(events=('lift','count'),mean_lift=('lift','mean'));summary.to_csv(out/'census_boundary_lift_summary.csv',index=False)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(out/'census_boundary_manifest.json').write_text(json.dumps({'official_url':'https://www2.census.gov/geo/tiger/TIGER2025/COUNTY/tl_2025_us_county.zip','archive_sha256':digest(archive),'original_sha256':digest(original),'frozen_scores_sha256':digest(frozen),'baseline_reproduced':True,'scope':'Post hoc centre reassignment and county repooling on frozen accepted 500m cells and candidate/outcome set; not rerunning pixel clipping or event selection.'},indent=2),encoding='utf8')
print(assignments.to_string(index=False));print(summary.to_string(index=False));print(metrics.to_string(index=False))
