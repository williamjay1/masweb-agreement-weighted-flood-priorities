"""Stream verified SWOT PIXC water detections into fixed 30 m optical cells.

Run only with a manifest of exact NASA checksums. Missing or checksum-failing files
are skipped. Water not found in PIXC is UNKNOWN, never a dry classification.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re
from pathlib import Path
import h5py
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'SWOT_PIXC_granule_manifest.csv'
RAW = HERE.parents[1] / 'external/data/swot_pixc'
OPTICAL = HERE.parent / 'new_review_analyses/sar_followup/missouri_followup/rtc_may26_point_samples.csv'
NOMINAL = HERE.parent / 'missouri_neartime_20261115/swot/point_nominal_footprint_membership.csv'
FIELDS = ('latitude','longitude','classification','classification_qual','geolocation_qual')
CLASSES = (3,4,5)
SCENARIOS = ('strict','sensitivity_prior_unwrap')


def md5(path):
    h = hashlib.md5()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def load_sample(optical, nominal):
    x = pd.read_csv(optical, usecols=['x','y','s30','l30'])
    n = pd.read_csv(nominal)
    if len(x) != len(n) or not np.allclose(x[['x','y']], n[['x_epsg5070','y_epsg5070']], atol=1e-6, rtol=0):
        raise ValueError('Optical and nominal samples differ in geometry or order')
    if not np.array_equal(x[['s30','l30']].to_numpy(), n[['s30','l30']].to_numpy()):
        raise ValueError('Optical and nominal classifications differ')
    if x[['x','y']].duplicated().any() or not x[['s30','l30']].isin([0,1]).all().all():
        raise ValueError('Duplicate sample coordinates or nonbinary optical classes')
    for p in ('033_259','033_272'):
        col = 'in_nominal_' + p
        if n[col].dtype != bool:
            d = n[col].astype(str).str.lower()
            if not d.isin(['true','false']).all():
                raise ValueError('Invalid nominal membership')
            x[col] = d.eq('true')
        else:
            x[col] = n[col]
    return x


def attr(v):
    a = np.asarray(v)
    if a.size == 1: return attr(a.item()) if isinstance(a.item(), (np.ndarray, np.generic)) else a.item()
    if a.dtype.kind in 'SU': return [str(z) for z in a.tolist()]
    return a.tolist()


def good_fill(raw, ds):
    ok = np.ones(raw.shape, dtype=bool)
    for key in ('_FillValue', 'missing_value'):
        if key in ds.attrs:
            for fill in np.asarray(ds.attrs[key]).ravel():
                if np.issubdtype(raw.dtype, np.floating) and np.isnan(fill): ok &= ~np.isnan(raw)
                else: ok &= raw != fill
    return ok


def transformed(raw, ds):
    # NetCDF packing attributes, when present, are applied only after raw fill screening.
    return raw.astype(np.float64) * float(ds.attrs.get('scale_factor',1)) + float(ds.attrs.get('add_offset',0))


def analyze_one(path, sample, orbit, chunksize=250_000):
    n = len(sample)
    counts = np.zeros((n,len(CLASSES),len(SCENARIOS)), dtype=np.int64)
    stats = {'input_points':0,'valid_raw_points':0,'screened_water_345':0,
             'matching_point_cell_incidences':0,'boundary_points_multiple_cells':0,
             'quality_pass_by_class':{q:{str(c):0 for c in CLASSES} for q in SCENARIOS},
             'matched_incidences_by_class':{q:{str(c):0 for c in CLASSES} for q in SCENARIOS}}
    col = 'in_nominal_'+orbit
    if col not in sample: raise ValueError('Unknown orbit '+orbit)
    xy = sample[['x','y']].to_numpy(dtype='float64')
    subset = np.flatnonzero(sample[col].to_numpy(dtype=bool))
    if not len(subset): raise ValueError('No optical samples in nominal footprint for '+orbit)
    tree = cKDTree(xy[subset])
    lo = xy[subset].min(axis=0)-15.001; hi = xy[subset].max(axis=0)+15.001
    to5070 = Transformer.from_crs(4326,5070,always_xy=True)
    with h5py.File(path, 'r') as h:
        g = h['pixel_cloud']
        ds = {k:g[k] for k in FIELDS}
        lengths = {len(v) for v in ds.values()}
        if len(lengths)!=1: raise ValueError('PIXC dataset lengths differ')
        attrs = {k:{str(a):attr(v) for a,v in ds[k].attrs.items()} for k in FIELDS}
        total = len(ds['latitude'])
        for start in range(0,total,chunksize):
            arr={k:v[start:start+chunksize] for k,v in ds.items()}
            size=len(arr['latitude']); stats['input_points']+=size
            valid=np.ones(size,dtype=bool)
            for k in FIELDS: valid &= good_fill(arr[k], ds[k])
            lat=transformed(arr['latitude'],ds['latitude']); lon=transformed(arr['longitude'],ds['longitude'])
            valid &= np.isfinite(lat)&np.isfinite(lon)&(lat>=-90)&(lat<=90)&(lon>=-180)&(lon<=180)
            stats['valid_raw_points']+=int(valid.sum())
            cls=arr['classification']
            valid &= np.isin(cls,CLASSES)
            if not valid.any(): continue
            cq=arr['classification_qual'][valid].astype(np.uint64)
            gq=arr['geolocation_qual'][valid].astype(np.uint64)
            # Exploratory sensitivity devised AFTER inspection of the first
            # granule: classification bit 4 denotes detected water without
            # prior water; geolocation bit 4 denotes suspect phase unwrapping.
            # Both can affect validity; report separately, never as good data.
            masks={
                'strict':(cq==0)&(gq==0),
                'sensitivity_prior_unwrap':((cq & ~np.uint64(4))==0)&((gq & ~np.uint64(4))==0),
            }
            cls_valid=cls[valid]
            for q,mask in masks.items():
                for c in CLASSES:
                    stats['quality_pass_by_class'][q][str(c)]+=int(np.count_nonzero(mask&(cls_valid==c)))
            keep=masks['sensitivity_prior_unwrap']
            stats['screened_water_345']+=int(keep.sum())
            if not keep.any(): continue
            lon_valid=lon[valid][keep]; lat_valid=lat[valid][keep]
            xx,yy=to5070.transform(lon_valid,lat_valid); xx=np.asarray(xx); yy=np.asarray(yy)
            cc=cls_valid[keep]; is_strict=masks['strict'][keep]
            in_box=np.isfinite(xx)&np.isfinite(yy)&(xx>=lo[0])&(xx<=hi[0])&(yy>=lo[1])&(yy<=hi[1])
            if not in_box.any(): continue
            points=np.column_stack((xx[in_box],yy[in_box])); cc=cc[in_box]; is_strict=is_strict[in_box]
            # Chebyshev radius exactly represents the 30 m square. Explicitly
            # include all cells on shared boundaries rather than arbitrary ties.
            matches=tree.query_ball_point(points, r=15.0, p=np.inf, workers=1)
            for local_indices,c,strict in zip(matches,cc,is_strict):
                if not local_indices: continue
                if len(local_indices)>1: stats['boundary_points_multiple_cells']+=1
                ids=subset[np.asarray(local_indices,dtype=int)]
                j=CLASSES.index(int(c))
                for k,q in enumerate(SCENARIOS):
                    if q=='strict' and not strict: continue
                    np.add.at(counts[:,j,k],ids,1)
                    stats['matched_incidences_by_class'][q][str(int(c))]+=len(ids)
                stats['matching_point_cell_incidences']+=len(ids)
    return counts, stats, attrs


def run(manifest,raw,optical,nominal,out,chunksize):
    out.mkdir(parents=True,exist_ok=True)
    sample=load_sample(optical,nominal)
    m=pd.read_csv(manifest,keep_default_na=False)
    for col in ('filename','bytes','md5_nasa','tile'):
        if col not in m: raise ValueError('Manifest missing '+col)
    if m.filename.duplicated().any(): raise ValueError('Duplicate manifest filenames')
    totals={p:np.zeros((len(sample),len(CLASSES),len(SCENARIOS)),dtype=np.int64) for p in ('033_259','033_272')}
    status=[]
    for _,row in m.iterrows():
        name=str(row.filename)
        if Path(name).name!=name or not name.endswith('.nc'): raise ValueError('Unsafe manifest name')
        orbit='_'.join(str(row.tile).split('_')[:2])
        if orbit not in totals: raise ValueError('Unsupported manifest orbit')
        record={'filename':name,'tile':str(row.tile),'expected_bytes':int(row['bytes']),'expected_md5':str(row.md5_nasa).lower()}
        path=raw/name
        if not path.is_file(): record['status']='missing'; status.append(record); continue
        record['actual_bytes']=path.stat().st_size
        if record['actual_bytes']!=record['expected_bytes']:
            record['status']='size_mismatch'; status.append(record); continue
        record['actual_md5']=md5(path)
        if record['actual_md5']!=record['expected_md5']:
            record['status']='md5_mismatch'; status.append(record); continue
        try:
            counts,stats,attrs=analyze_one(path,sample,orbit,chunksize)
        except Exception as exc:
            record['status']='analysis_error'; record['error']=str(exc); status.append(record); continue
        totals[orbit]+=counts
        record.update(status='analyzed',stats=stats,attributes=attrs)
        status.append(record)
        print(f"Analyzed {name}: {stats['input_points']} PIXC points",flush=True)
    # A cell may contain classes 3, 4, and/or 5; they are not mutually exclusive.
    obs=sample.copy()
    for p,counts in totals.items():
        for k,q in enumerate(SCENARIOS):
            for j,c in enumerate(CLASSES): obs[f'pass_{p}_{q}_class_{c}_points']=counts[:,j,k]
            obs[f'pass_{p}_{q}_main_water_detected']=counts[:,:2,k].sum(axis=1)>0
            obs[f'pass_{p}_{q}_water_345_detected']=counts[:,:,k].sum(axis=1)>0
    for q in SCENARIOS:
        for mode in ('main_water_detected','water_345_detected'):
            obs[f'either_pass_{q}_{mode}']=obs[f'pass_033_259_{q}_{mode}']|obs[f'pass_033_272_{q}_{mode}']
    obs.to_csv(out/'optical_cells_detected_water.csv',index_label='sample_id')
    by=[]
    for p in ('033_259','033_272','either'):
        for q in SCENARIOS:
            for mode in ('main_water_detected','water_345_detected'):
                key=('either_pass_' if p=='either' else 'pass_'+p+'_')+q+'_'+mode
                sel=obs[key]
                by.append({'scope':p, 'analyzed_files':sum(x['status']=='analyzed' and (p=='either' or x['tile'].startswith(p+'_')) for x in status), 'expected_files':sum(p=='either' or x['tile'].startswith(p+'_') for x in status), 'quality_scenario':q,'class_scenario':mode,'unique_optical_cells_with_detected_water':int(sel.sum()),
                           's30_water_cells':int((sel&(obs.s30==1)).sum()),
                           'l30_water_cells':int((sel&(obs.l30==1)).sum()),
                           'both_optical_water_cells':int((sel&(obs.s30==1)&(obs.l30==1)).sum())})
    pd.DataFrame(by).to_csv(out/'detected_water_optical_counts.csv',index=False)
    final={'interpretation':'Positive water detections only; non-detections are unknown, not dry. Optical data are 2025-05-30, SWOT data 2025-05-28, outside original event window.',
           'sensitivity_note':'Exploratory after first granule inspection: allow classification bit 4 (detected water without prior water) and geolocation bit 4 (suspect phase unwrapping); results flagged uncertain and not a preplanned sensitivity.',
           'status_counts':pd.Series([x['status'] for x in status]).value_counts().to_dict(),
           'manifest_files':len(status),'files':status,'summary':by}
    (out/'run_provenance.json').write_text(json.dumps(final,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
    print(json.dumps({'status_counts':final['status_counts'],'manifest_files':len(status)},ensure_ascii=False),flush=True)
    return final


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,default=MANIFEST); p.add_argument('--raw',type=Path,default=RAW)
    p.add_argument('--optical',type=Path,default=OPTICAL); p.add_argument('--nominal',type=Path,default=NOMINAL)
    p.add_argument('--out',type=Path,default=HERE/'outputs'); p.add_argument('--chunksize',type=int,default=250000)
    a=p.parse_args()
    if a.chunksize<=0: p.error('chunksize must be positive')
    run(a.manifest,a.raw,a.optical,a.nominal,a.out,a.chunksize)
if __name__=='__main__': main()

