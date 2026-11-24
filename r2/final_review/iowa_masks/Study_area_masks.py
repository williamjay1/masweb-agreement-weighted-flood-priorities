"""Rebuild Appendix Figure A1 from the frozen 500 m cells and native 30 m rasters."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.windows import Window
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import Patch, Rectangle

sys.path.insert(0, r'external/tools/.agents/skills/sci-figures')
from figstyle import apply_house_style, audit, mm

PROJECT = Path('external/analysis/Geocarto_R2_20261115')
OUT = Path(__file__).resolve().parent
BASE = Path('external/analysis/Geocarto_R1_20261008_NatureStyle/audit')
ORIGINAL = Path('external/prior/sci/remote_sensing_sci_novelty_audit/candidate3_agricultural_hazard_cascade/revision_geocarto_v4')
SOURCE = BASE / 'reproducibility/inputs/results/analysis/blind_common_support/cells'
COUNTIES = ORIGINAL / 'release/MASWEB_v2_anonymous/data/raw/census_counties_2025/counties_2025_semigeneral.geojson'
COUNTY_SCORES = BASE / 'support_sensitivity/county_scores_and_selections.csv'
RASTERS = PROJECT / 'viirs_noaa_formula_20261124/integration/work/supplementary_analysis/new_review_analyses/event_figures/inputs/raster_cache'
EVENT = 'N2024_191762_IOWA'
EVENTS = ['Minnesota', 'Wisconsin', 'South Dakota', 'Iowa', 'Missouri']
WATER, DRY, OUTSIDE = '#175B83', '#C7D4D9', '#F8F8F6'


def accepted_datasets():
    scores = pd.read_csv(COUNTY_SCORES, dtype={'county_fips': str})
    scores = scores[scores.threshold.eq(.95)]
    files = sorted(SOURCE.glob('*.parquet'))
    datasets = {}
    for path in files:
        d = pd.read_parquet(path)
        d = d.loc[d.eligible_pixel_count.gt(0) & d.strict_common_valid_coverage.ge(.95)].copy()
        event = d.event_id.iloc[0]
        name = next(name for name in EVENTS if event.endswith(name.upper().replace(' ', '')))
        datasets[name] = (event, d, scores.loc[scores.event_id.eq(event), 'county_fips'].tolist())
    assert set(datasets) == set(EVENTS)
    assert sum(len(d) for _, d, _ in datasets.values()) == 44_510
    return datasets, files


def county_paths():
    transform = Transformer.from_crs(4326, 5070, always_xy=True)
    features = json.loads(COUNTIES.read_text(encoding='utf-8'))['features']
    return {f['properties']['FIPS']: (f['geometry'], transform) for f in features}


def county_boundary(ax, fips, by_id):
    lines = []
    for code in fips:
        geometry, tr = by_id[code]
        polys = geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]
        for poly in polys:
            for ring in poly:
                a = np.asarray(ring)
                x, y = tr.transform(a[:, 0], a[:, 1])
                lines.append(np.column_stack([x, y]))
    ax.add_collection(LineCollection(lines, colors='#828D93', linewidths=.47, zorder=1))


def extract_pair(cells):
    suffixes = ('S30_state', 'L30_state', 'lagged_eligibility')
    sources = [RASTERS / f'{EVENT}_{suffix}_EPSG5070_30m.tif' for suffix in suffixes]
    crop_cell = cells.sort_values(['strict_union_pixel_count', 'x_index', 'y_index'], ascending=[False, True, True]).iloc[0]
    with rasterio.open(sources[0]) as s30, rasterio.open(sources[1]) as l30, rasterio.open(sources[2]) as elig:
        assert s30.transform == l30.transform == elig.transform
        assert s30.shape == l30.shape == elig.shape
        assert s30.crs == l30.crs == elig.crs and s30.crs.to_epsg() == 5070
        assert s30.transform.a == 30 and s30.transform.e == -30
        r, c = s30.index(crop_cell.x_center_m, crop_cell.y_center_m)
        ncol, nrow = 260, 128
        window = Window(c-ncol//2, r-nrow//2, ncol, nrow)
        assert 0 <= window.col_off and window.col_off+ncol <= s30.width
        assert 0 <= window.row_off and window.row_off+nrow <= s30.height
        s, qs = s30.read([2, 4], window=window)
        l, ql = l30.read([2, 4], window=window)
        e = elig.read(6, window=window) == 1
        left, bottom, right, top = rasterio.windows.bounds(window, s30.transform)

    xv = np.floor((left+(np.arange(ncol)+.5)*30)/500).astype(int)
    yv = np.floor((top-(np.arange(nrow)+.5)*30)/500).astype(int)
    key = pd.MultiIndex.from_product([yv, xv], names=['y_index', 'x_index'])
    accepted = key.isin(cells.set_index(['y_index', 'x_index']).index).reshape(nrow, ncol)
    support = e & accepted & (s <= 1) & (l <= 1)
    support &= ((qs & 127) == 0) & ((qs & 128) != 0) & ((ql & 127) == 0) & ((ql & 128) != 0)
    stats = {
        'eligible_joint_valid_pixels_in_accepted_cells': int(support.sum()),
        's30_water_pixels': int(np.sum(support & (s == 1))),
        'l30_water_pixels': int(np.sum(support & (l == 1))),
        'both_water_pixels': int(np.sum(support & (s == 1) & (l == 1))),
        'either_water_pixels': int(np.sum(support & ((s == 1) | (l == 1)))),
    }
    central = (xv[None, :] == crop_cell.x_index) & (yv[:, None] == crop_cell.y_index)
    assert np.sum(support & central) == crop_cell.strict_common_valid_pixel_count
    assert np.sum(support & central & (s == 1)) == crop_cell.strict_s30_water_pixel_count
    assert np.sum(support & central & (l == 1)) == crop_cell.strict_l30_water_pixel_count
    assert 0 < stats['both_water_pixels'] < stats['either_water_pixels']
    return [np.where(support, z, 255) for z in (s, l)], sources, (left, bottom, right, top), stats, dict(
        col_offset=int(window.col_off), row_offset=int(window.row_off), width=ncol, height=nrow,
        central_cell_x_index=int(crop_cell.x_index), central_cell_y_index=int(crop_cell.y_index),
    )


def paint_mask(ax, image, bounds):
    left, bottom, right, top = bounds
    ax.set_facecolor(OUTSIDE)
    for value, colour in [(0, DRY), (1, WATER)]:
        rects = []
        for row, line in enumerate(image):
            edges = np.flatnonzero(np.diff(np.r_[False, line == value, False]))
            y = top-row*30
            for lo, hi in edges.reshape(-1, 2):
                x1, x2 = left+lo*30, left+hi*30
                rects.append(((x1, y), (x2, y), (x2, y-30), (x1, y-30)))
        ax.add_collection(PolyCollection(rects, facecolors=colour, edgecolors='none', antialiaseds=False))
    ax.set(xlim=(left, right), ylim=(bottom, top))


def clean(ax):
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color('#A8B2B8')
        spine.set_linewidth(.55)


def main():
    datasets, cell_files = accepted_datasets()
    iowa = datasets['Iowa'][1]
    masks, rasters, bounds, stats, window = extract_pair(iowa)
    by_id = county_paths()
    plt = apply_house_style(fontsize=8)
    plt.rcParams.update({'font.family':'Arial', 'savefig.bbox':'standard'})
    fig = plt.figure(figsize=(mm(183), mm(112)), facecolor='white')
    fig.text(.025,.966,'a',fontsize=11,weight='bold',va='center')
    fig.text(.053,.966,'Primary events and accepted agricultural cells',fontsize=9,weight='bold',va='center')

    summaries = fig.add_gridspec(1,5,left=.025,right=.975,bottom=.584,top=.843,wspace=.18)
    mark_colour='#AB6329'
    for i,name in enumerate(EVENTS):
        _, cells, fips = datasets[name]
        ax = fig.add_subplot(summaries[0,i])
        county_boundary(ax, fips, by_id)
        ax.scatter(cells.x_center_m,cells.y_center_m,s=.36,c='#4F8297',marker='s',linewidths=0,zorder=2)
        if name=='Iowa':
            l,b,r,t=bounds
            ax.add_patch(Rectangle((l,b),r-l,t-b,facecolor='none',edgecolor=mark_colour,linewidth=.92,zorder=4))
        pos = ax.get_position(original=True)
        xc = (pos.x0+pos.x1)/2
        fig.text(xc,.913,name,fontsize=8.5,weight='bold',ha='center',va='center')
        fig.text(xc,.879,f'{len(cells):,} cells',fontsize=7.4,ha='center',va='center')
        clean(ax)
        ax.autoscale_view()
        ax.margins(.055)

    overview_legend = [
        Patch(facecolor='#4F8297', label='Accepted 500 m cell centres'),
        Patch(facecolor='none',edgecolor='#828D93',linewidth=.65, label='Generalized county boundaries'),
        Patch(facecolor='none',edgecolor=mark_colour, linewidth=.85, label='Iowa zoom area'),
    ]
    fig.legend(handles=overview_legend,loc='center left',bbox_to_anchor=(.024,.538),ncols=3,
               fontsize=7.1,frameon=False,borderaxespad=0,handlelength=1.2,columnspacing=1.5)

    fig.text(.025,.471,'b',fontsize=11,weight='bold',va='center')
    fig.text(.053,.471,'Iowa, S30 water mask',fontsize=9,weight='bold',va='center')
    fig.text(.514,.471,'c',fontsize=11,weight='bold',va='center')
    fig.text(.542,.471,'Iowa, L30 water mask',fontsize=9,weight='bold',va='center')
    maps=fig.add_gridspec(1,2,left=.025,right=.975,bottom=.110,top=.436,wspace=.055)
    for i,image in enumerate(masks):
        ax=fig.add_subplot(maps[0,i])
        paint_mask(ax,image,bounds)
        clean(ax)

    lg=[Patch(facecolor=WATER,label='Mapped water'),Patch(facecolor=DRY,label='Mapped dry'),
        Patch(facecolor=OUTSIDE,edgecolor='#A8B2B8',linewidth=.5,label='Outside joint support')]
    fig.legend(handles=lg,loc='center left',bbox_to_anchor=(.024,.067),ncols=3,fontsize=7.3,
               frameon=False,borderaxespad=0,handlelength=1.3,columnspacing=1.6)
    fig.canvas.draw()
    sharer=fig.get_axes()[-1]
    x0,y0,x1,y1=sharer.get_position().extents
    bar_width=(x1-x0)*1000/(bounds[2]-bounds[0])
    fig.add_artist(plt.Line2D([.817,.817+bar_width],[.065,.065],transform=fig.transFigure,
                            color='#243137',linewidth=1.2,solid_capstyle='butt'))
    fig.text(.824+bar_width,.065,'1 km',fontsize=7.3,va='center')

    report=audit(fig, verbose=False)
    assert report['ok'],report
    report['minimum_visible_font_pt'] = min(t.get_fontsize() for t in fig.findobj(plt.Text) if t.get_visible() and t.get_text().strip())
    assert report['minimum_visible_font_pt'] >= 5
    stem=OUT/'FigureA1_Study_area'
    for ext in ('pdf','svg'):
        fig.savefig(stem.with_suffix('.'+ext),facecolor='white')
    fig.savefig(stem.with_suffix('.png'),facecolor='white',dpi=180)
    fig.savefig(stem.with_suffix('.tif'),facecolor='white',dpi=1200,pil_kwargs={'compression':'tiff_lzw'})
    np.savez_compressed(OUT/'iowa_30m_mask_zoom.npz', s30=masks[0], l30=masks[1], bounds_5070=bounds, pixel_size_m=30)
    report = {key: value.item() if isinstance(value, np.generic) else value for key, value in report.items()}
    metadata={
        'accepted_cell_counts': {n: len(d) for n,(_,d,_) in datasets.items()},
        'projection': 'EPSG:5070', 'pixel_size_m': 30, 'bounds': bounds, 'window':window,
        'crop_rule':'Illustrative fixed-size crop centred on the accepted Iowa cell with the largest common-valid mapped water union, ties ordered by x and y cell indices.',
        'acquisition_utc':{'S30':'2024-05-25T16:58:49Z','L30':'2024-05-25T16:58:28Z'},
        'crop_counts': stats, 'figure_audit':report,
        'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*cell_files,COUNTIES,COUNTY_SCORES,*rasters]},
    }
    (OUT/'FigureA1_Study_area_manifest.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps({**stats,'bounds':bounds,'window':window,'fig_audit':report},indent=2))


if __name__ == '__main__':
    main()
