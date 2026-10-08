"""Render the six study figures from the frozen numerical evidence.

Production uses SciencePlots 2.2.2 science/nature/no-latex.
Portable reruns use bundled rcParams and need Matplotlib, NumPy and Pillow.
This renderer performs no scientific analysis or bootstrap.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent if HERE.name in ('scripts','code') else HERE
DEFAULT_INPUT = ROOT/'data/derived/figures_inputs' if HERE.name in ('scripts','code') else HERE/'figures_inputs'
DEFAULT_OUTPUT = ROOT/'figures' if HERE.name in ('scripts','code') else HERE/'figures'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-dir', type=Path, default=DEFAULT_INPUT)
parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
parser.add_argument('--figures', nargs='+', type=int, choices=range(1,7), default=[1,2,3,4,5,6])
parser.add_argument('--use-scienceplots', action='store_true')
ARGS = parser.parse_args()
INPUT, OUT = ARGS.input_dir.resolve(), ARGS.output_dir.resolve()
OUT.mkdir(parents=True, exist_ok=True)
os.environ['MPLCONFIGDIR'] = str(OUT/'_render_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import findfont
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
from matplotlib.text import Text
import numpy as np
from PIL import Image
STYLE_MODE = 'bundled SciencePlots-derived rcParams'
if ARGS.use_scienceplots:
    import scienceplots
    assert importlib.metadata.version('SciencePlots') == '2.2.2'
    plt.style.use(['science','nature','no-latex'])
    STYLE_MODE = 'SciencePlots 2.2.2: science + nature + no-latex'
plt.rcParams.update(json.loads((INPUT/'figure_style.json').read_text(encoding='utf-8')))
BLUE, VERMILLION, GREEN, PURPLE = '#0072B2','#D55E00','#009E73','#A15D8E'
GRAY, INK, PALE = '#7C8489','#1A1A1A','#F1F3F4'
SCALES = np.array([.5,1,2,5,10,20,30])
EVENTS = {
 'N2023_179508_MINNESOTA': ('Minnesota 2023',BLUE,'o','-'),
 'N2023_179829_WISCONSIN': ('Wisconsin 2023',VERMILLION,'s','--'),
 'N2023_180114_SOUTHDAKOTA': ('South Dakota 2023',GREEN,'^','-.'),
 'N2024_191762_IOWA': ('Iowa 2024',PURPLE,'D',':'),
 'N2025_202615_MISSOURI': ('Missouri 2025','#9A7600','v',(0,(5,2))),
}
MANIFEST = []
def read_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))
def col(rows,key):
    return np.array([float(row[key]) for row in rows])
def mm(value):
    return value/25.4
def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def data_copy(frame,name):
    dest=OUT/'_source_data'/name
    dest.parent.mkdir(exist_ok=True)
    with dest.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(frame[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(frame)
    return dest
def layout_report(fig):
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    tight=fig.get_tightbbox(renderer)
    texts=[t for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()]
    minimum=min(t.get_fontsize() for t in texts)
    bounds=[(t,t.get_window_extent(renderer)) for t in texts]
    outside=[t.get_text() for t,b in bounds if b.x0 < -1 or b.y0 < -1 or b.x1 > fig.bbox.width+1 or b.y1 > fig.bbox.height+1]
    overlaps=[]
    for i,(t1,b1) in enumerate(bounds):
        for t2,b2 in bounds[i+1:]:
            if min(b1.x1,b2.x1)-max(b1.x0,b2.x0) > .6 and min(b1.y1,b2.y1)-max(b1.y0,b2.y0) > .6:
                overlaps.append([t1.get_text(),t2.get_text()])
    nominal=[float(v*25.4) for v in fig.get_size_inches()]
    return {'nominal_mm':nominal,'tight_mm':[tight.width*25.4,tight.height*25.4],
            'min_font_pt':minimum,'pdf_fonttype':int(plt.rcParams['pdf.fonttype']),
            'texts_outside_canvas':outside,'text_intersections':overlaps,
            'ok':nominal[0] <=183.01 and nominal[1] <=170.01 and tight.width*25.4 <=183.5
                 and minimum>=8 and plt.rcParams['pdf.fonttype']==42 and not outside and not overlaps}
def finish(fig,stem,sources,note):
    report=layout_report(fig)
    assert report['ok'],(stem,report)
    fig.savefig(OUT/f'{stem}.png',dpi=180,facecolor='white')
    fig.savefig(OUT/f'{stem}.pdf',facecolor='white',metadata={'Title':stem.replace('_',' '),'Subject':'Frozen results; editable vector artwork'})
    fig.savefig(OUT/f'{stem}.svg',facecolor='white')
    fig.savefig(OUT/f'{stem}.tif',dpi=1200,facecolor='white',pil_kwargs={'compression':'tiff_lzw'})
    with Image.open(OUT/f'{stem}.tif') as im:
        raster={'size_px':list(im.size),'dpi':[float(d) for d in im.info.get('dpi',())]}
        assert len(raster['dpi'])==2 and all(abs(d-1200)<.01 for d in raster['dpi'])
    MANIFEST.append({'figure':stem,'dimensions_mm':list(np.round(fig.get_size_inches()*25.4,2)),
                     'min_font_pt':report['min_font_pt'],'layout_report':report,
                     'native_tiff':raster,'source_files':[p.name for p in sources],
                     'source_sha256':{p.name:sha256(p) for p in sources},'style_mode':STYLE_MODE,
                     'font_file_used':findfont('Arial'),'note':note,'visual_review':'pending view_image review'})
    plt.close(fig)
    print(stem,'rendered',raster['size_px'],flush=True)
def panels(height=88,bottom=.25,top=.83,left=.095,right=.975,gap=.36):
    fig,axes=plt.subplots(1,2,figsize=(mm(183),mm(height)))
    fig.subplots_adjust(left=left,right=right,bottom=bottom,top=top,wspace=gap)
    for ax in axes:
        ax.tick_params(length=3,width=.6,pad=3);ax.grid(False)
    return fig,axes
def heading(ax,label,title,label_x=-.14):
    ax.text(label_x,1.125,label,transform=ax.transAxes,fontsize=10,fontweight='bold',ha='left',va='center',color=INK)
    ax.text(0,1.125,title,transform=ax.transAxes,fontsize=8.5,fontweight='bold',ha='left',va='center',color=INK)
def scale_axis(ax,low_n=False):
    ax.set_xlim(-.2,6.2)
    ax.set_xticks(np.arange(7),['0.5','1','2','5','10','20','30'])
    ax.set_xlabel('Aggregation scale (km)',labelpad=5)
    if low_n:ax.axvspan(4.5,6.2,color=PALE,zorder=-2)
def outside_legend(fig,handles,labels,ncol=2,y=.02):
    return fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.51,y),ncol=ncol,
                      fontsize=8,handlelength=2.6,handletextpad=.6,columnspacing=2.4,labelspacing=.65)
def figure1(args):
    """Draw the study workflow in physical millimetres; no analysis is run.

    Text is measured against its containing region and every connector is
    checked against every text extent. The two analysis routes begin directly
    at common 500 m support; RMA appears only after county scoring/allocation.
    """
    from matplotlib.patches import Rectangle, FancyArrowPatch, Polygon
    from matplotlib.transforms import Bbox

    width, height = 183, 161
    fig = plt.figure(figsize=(mm(width), mm(height)))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, width), ylim=(height, 0))
    ax.axis('off')
    blue, green = '#246F91', '#387A67'
    edge, link, muted = '#CCD2D6', '#64717A', '#4D5960'
    tracked, segments = [], []

    def text(x, y, string, *, size=8.2, bold=False, color=INK, region=None):
        obj = ax.text(x, y, string, fontsize=size, fontweight='bold' if bold else 'normal',
                      color=color, ha='left', va='top', linespacing=1.30, zorder=5)
        if region:
            tracked.append((obj, region))
        return obj

    def region(x, y, w, h, face='white', border=edge, lw=.65):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=face,
                               edgecolor=border, lw=lw, zorder=0))
        return (x, y, x+w, y+h)

    def line(x1, y1, x2, y2, color=link, lw=.75):
        ax.plot([x1, x2], [y1, y2], color=color, lw=lw,
                solid_capstyle='butt', zorder=1)
        segments.append(((x1, y1), (x2, y2)))

    def arrow(x1, y1, x2, y2, color=link):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                                    mutation_scale=7, linewidth=.75, color=color,
                                    shrinkA=0, shrinkB=0, zorder=2))
        segments.append(((x1, y1), (x2, y2)))

    def heading(x, y, label, title, color=INK, container=None):
        text(x, y-.25, label, size=10, bold=True, region=container)
        text(x+7.2, y, title, size=9, bold=True, color=color, region=container)

    # a. Matched observation inputs, with explicit eligibility and alignment.
    heading(4, 4, 'a', 'Paired observations and common agricultural support')
    land = region(4, 12, 84, 21, face='#F6F7F8')
    water = region(95, 12, 84, 21, face='#F6F7F8')
    text(8, 15, 'Agricultural eligibility', size=8.7, bold=True, region=land)
    text(8, 21, 'CDL corn or soybean in ≥2 of 3 prior years', region=land)
    text(8, 25, 'Valid GSW; persistent water excluded', region=land)
    text(8, 29, 'Within the selected event domains', region=land)
    text(99, 15, 'Paired optical water observations', size=8.7, bold=True, region=water)
    text(99, 21, 'DSWx S30 / L30 · nominal 30 m', region=water)
    text(99, 25, 'Same UTC date; shared valid observations', region=water)
    text(99, 29, 'Nearest neighbour alignment to EPSG:5070', region=water)
    arrow(46, 33, 46, 39)
    arrow(137, 33, 137, 39)

    support = region(4, 39, 175, 18, face='#EEF5F8', border='#A8BEC8')
    left = (4, 39, 130, 57)
    right = (133, 39, 179, 57)
    text(8, 42, 'Common agricultural support · 500 m cells', size=8.8,
         bold=True, color=blue, region=left)
    text(8, 48, 'Pixel centre assignment; pool water and eligible counts', region=left)
    text(8, 52, 'Common valid / eligible ≥95%', region=left)
    line(131, 42, 131, 52, color='#BACBD2', lw=.6)
    text(136, 42, 'Five primary events', size=8.2, color=muted, region=right)
    text(136, 47.6, '44,510 cells', size=11, bold=True, color=blue, region=right)

    # A common branch point precedes two equal, clearly separated routes.
    line(91.5, 57, 91.5, 61)
    line(46, 61, 137, 61)
    arrow(46, 61, 46, 67, color=blue)
    arrow(137, 61, 137, 67, color=green)

    grid = region(4, 67, 84, 64)
    county = region(95, 67, 84, 64)
    line(4, 67, 88, 67, color=blue, lw=1.25)
    line(95, 67, 179, 67, color=green, lw=1.25)
    heading(8, 70, 'b', 'Multiscale target comparison', color=blue, container=grid)
    heading(99, 70, 'c', 'County priority evaluation', color=green, container=county)
    line(8, 76, 84, 76, color=edge, lw=.55)
    line(99, 76, 175, 76, color=edge, lw=.55)

    text(8, 80, 'Aggregate square units', size=8.6, bold=True, region=grid)
    text(8, 86, '0.5, 1, 2, 5, 10, 20 and 30 km', region=grid)
    text(8, 90, 'Recompute S30 and L30 water fractions', region=grid)
    arrow(46, 94, 46, 98, color=blue)
    text(8, 101, 'Compare ranks and selected targets', size=8.6, bold=True, region=grid)
    text(8, 107, 'Rank agreement: Spearman ρ', region=grid)
    text(8, 111, 'Target agreement: top 20% overlap', region=grid)
    text(8, 115, r'Selected units: $k = \lceil 0.20 \times n \rceil$', region=grid)
    line(8, 120, 84, 120, color=edge, lw=.55)
    text(8, 122.5, 'Five event summary', size=8.5, bold=True, color=blue, region=grid)
    text(8, 126.5, 'Event means and bootstrap intervals', region=grid)

    text(99, 80, 'Pool counts by county', size=8.6, bold=True, region=county)
    text(99, 86, 'Assign counties from 500 m cell centres', region=county)
    text(99, 90, 'Water, valid, intersection and union counts', region=county)
    arrow(137, 94, 137, 98, color=green)
    text(99, 101, 'AWC priority and county allocation', size=8.6, bold=True, region=county)
    text(99, 107, 'AWC = mean water fraction × Jaccard overlap', region=county)
    text(99, 111, 'Exact budget: 0.20 × n county equivalents', region=county)
    text(99, 115, 'Equal sharing at cutoff ties', region=county)
    line(99, 120, 175, 120, color=edge, lw=.55)
    text(99, 122.5, 'RMA indemnity capture and lift', size=8.5, bold=True,
         color=green, region=county)
    text(99, 126.5, 'Four events with positive RMA totals', region=county)

    # d. A scope strip, without implying one identical cohort for every check.
    checks = region(4, 136, 175, 22, face='#F6F7F8', border='#E1E4E6', lw=.6)
    heading(8, 139, 'd', 'Sensitivity and scope checks', container=checks)
    parts = [(8, 48), (52, 89), (93, 132), (137, 175)]
    captions = [
        ('Observation support', '90%, 95%, 99%', ''),
        ('Water formulations', 'DSWx, MNDWI, AWEI', ''),
        ('Within product stability', 'Rank persistence', 'Score dispersion'),
        ('County utility', 'Budget / exposure', 'Event sensitivity'),
    ]
    for (x, end), (title, body1, body2) in zip(parts, captions):
        r = (x-1, 144, end+1, 158)
        text(x, 145, title, size=8.3, bold=True, color=muted, region=r)
        text(x, 150, body1, region=r)
        if body2:
            text(x, 153.8, body2, region=r)
    for x in [49, 90, 134]:
        line(x, 145, x, 155, color='#DADEE1', lw=.6)

    # Region checks detect overflow into card margins, which a canvas-only
    # test misses. Expand text bounds by 0.35 pt for connector clearance.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    containment_failures, collisions = [], []
    for obj, r in tracked:
        pixels = ax.transData.transform([(r[0], r[1]), (r[2], r[3])])
        box = Bbox.from_extents(min(pixels[:, 0]), min(pixels[:, 1]),
                                max(pixels[:, 0]), max(pixels[:, 1]))
        actual = obj.get_window_extent(renderer)
        # Require at least 0.4 mm clearance from each containing edge.
        inset = fig.dpi * .4 / 25.4
        if actual.x0 < box.x0+inset or actual.x1 > box.x1-inset or \
           actual.y0 < box.y0+inset or actual.y1 > box.y1-inset:
            containment_failures.append(obj.get_text())
    all_texts = [t for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip()]
    margin = .35 * fig.dpi / 72
    for p1, p2 in segments:
        p1, p2 = ax.transData.transform([p1, p2])
        for obj in all_texts:
            bb = obj.get_window_extent(renderer)
            bb = Bbox.from_extents(bb.x0-margin, bb.y0-margin, bb.x1+margin, bb.y1+margin)
            if abs(p1[0]-p2[0]) < .01:
                hit = bb.x0 <= p1[0] <= bb.x1 and \
                    min(p1[1], p2[1]) <= bb.y1 and max(p1[1], p2[1]) >= bb.y0
            else:
                hit = bb.y0 <= p1[1] <= bb.y1 and \
                    min(p1[0], p2[0]) <= bb.x1 and max(p1[0], p2[0]) >= bb.x0
            if hit:
                collisions.append(obj.get_text())
    layout = {'text_region_clearance_mm': .4, 'text_connector_clearance_pt': .35,
              'texts_outside_containing_region': containment_failures,
              'text_line_intersections': collisions,
              'ok': not containment_failures and not collisions}
    assert layout['ok'], layout
    finish(fig, 'Figure1_Study_design',
           [INPUT/'sensor_acquisition_timestamps.csv'],
           'Common retained 500 m cells branch directly into grid target comparison and '
           'county priority evaluation. RMA is an external outcome; sensitivity checks retain '
           'their original cohort scopes.')
    MANIFEST[-1]['workflow_layout_report'] = layout

def figure2(args):
    source=INPUT/'results_table3_all5.csv'
    d=sorted(read_csv(source),key=lambda r:float(r['scale_km']))
    assert np.all(col(d,'event_count')==5) and np.allclose(col(d,'scale_km'),SCALES)
    data_copy(d,'Figure2_scale_summary.csv')
    fig,axes=panels(height=90,bottom=.27,top=.83)
    for i,(ax,metric,label,color,marker,title) in enumerate(zip(axes,['topk_overlap','spearman'],
        ['Top 20% overlap','Spearman ρ'],[BLUE,VERMILLION],['o','s'],['Target selection','Rank agreement'])):
        x=np.arange(7);y=col(d,f'{metric}_mean')
        ax.fill_between(x,col(d,f'{metric}_ci_low'),col(d,f'{metric}_ci_high'),color=color,alpha=.14,lw=0)
        ax.plot(x[:5],y[:5],color=color,lw=1.3)
        ax.plot(x[4:],y[4:],color=GRAY,lw=1.1,ls='--')
        ax.scatter(x[:5],y[:5],s=21,marker=marker,color=color,zorder=4)
        ax.scatter(x[5:],y[5:],s=23,marker=marker,color=GRAY,zorder=4)
        scale_axis(ax,True);ax.set_ylabel(label);ax.set_ylim(0,1.02);ax.set_yticks(np.arange(0,1.01,.2))
        heading(ax,chr(97+i),title)
    fig.text(.5,.095,'Five events; bands: 95% event bootstrap intervals (5,000 draws).',ha='center',fontsize=8,color=INK)
    fig.text(.5,.045,'Gray scales: ≥20 units in 4/5 events at 20 km and 2/5 at 30 km.',ha='center',fontsize=8,color=INK)
    finish(fig,'Figure2_Scale_response',[source],'Frozen five event means and 5,000 event bootstrap intervals. All five events retained at every scale.')
def figure3(args):
    source=INPUT/'historical_hls_sar_per_event_metrics.csv'
    d=[r for r in read_csv(source) if float(r['budget'])==.2]
    assert {r['event_id'] for r in d}==set(EVENTS) and len(d)==35
    data_copy(d,'Figure3_event_top20.csv')
    fig,axes=panels(height=105,bottom=.35,top=.85)
    for event,(name,color,marker,style) in EVENTS.items():
        g=sorted([r for r in d if r['event_id']==event],key=lambda r:float(r['scale_km']))
        for ax,metric in zip(axes,['topk_overlap','spearman']):
            ax.plot(np.arange(7),col(g,metric),label=name,color=color,marker=marker,ls=style,lw=1.1,ms=3.7,markeredgewidth=.5)
    for ax in axes:scale_axis(ax,True)
    axes[0].set_ylabel('Top 20% overlap');axes[0].set_ylim(-.04,1.055);axes[0].set_yticks(np.arange(0,1.01,.2))
    axes[1].set_ylabel('Spearman ρ');axes[1].set_ylim(-.42,1.055);axes[1].set_yticks([-.4,0,.4,.8,1])
    axes[1].axhline(0,color='#A9A9A9',lw=.55,zorder=0)
    heading(axes[0],'a','Target selection');heading(axes[1],'b','Rank agreement')
    h,l=axes[0].get_legend_handles_labels();outside_legend(fig,h,l,ncol=2,y=.014)
    finish(fig,'Figure3_Event_heterogeneity',[source],'All five primary event trajectories at 20% budget; distinctive colors, markers and line styles.')
def figure4(args):
    source,report=INPUT/'spatial_mechanisms_summary.csv',INPUT/'spatial_mechanisms_report.json'
    assert json.loads(report.read_text())['bootstrap_repetitions']==5000
    d=sorted(read_csv(source),key=lambda r:float(r['scale_km']));assert np.all(col(d,'event_count')==5)
    data_copy(d,'Figure4_mechanism_summary.csv')
    fig,axes=panels(height=93,bottom=.28,top=.83)
    for product,color,marker,ls in [('s30',BLUE,'o','-'),('l30',VERMILLION,'s','--')]:
        for ax,metric in zip(axes,['rank_persistence','sd_ratio']):
            key,x=f'{product}_{metric}',np.arange(7)
            ax.fill_between(x,col(d,f'{key}_ci_low'),col(d,f'{key}_ci_high'),color=color,alpha=.13,lw=0)
            ax.plot(x,col(d,f'{key}_mean'),label=product.upper(),color=color,marker=marker,lw=1.2,ms=3.7,ls=ls)
    for ax in axes:
        scale_axis(ax);ax.axhline(1,color='#A9A9A9',lw=.6,ls=':',zorder=0)
    axes[0].set_ylim(0,1.06);axes[0].set_yticks(np.arange(0,1.01,.2))
    axes[1].set_ylim(0,1.3);axes[1].set_yticks([0,.4,.8,1.2])
    axes[0].set_ylabel('Rank persistence (ρ)');axes[1].set_ylabel('Score SD / 500 m score SD')
    heading(axes[0],'a','Within product rank persistence');heading(axes[1],'b','Within product score dispersion')
    h,l=axes[0].get_legend_handles_labels();outside_legend(fig,h,l,y=.066)
    fig.text(.5,.025,'Five events; bands: 95% event bootstrap intervals (5,000 draws).',ha='center',fontsize=8,color=INK)
    finish(fig,'Figure4_Mechanism_diagnostics',[source,report],'Separate S30/L30 rank persistence and within product SD ratio; original 5,000 event bootstrap intervals.')
def figure5(args):
    source=INPUT/'results_algorithm_top20.csv';d=read_csv(source)
    assert np.all(col(d,'budget')==.2) and np.all(col(d,'overlap_min_units')==10)
    data_copy(d,'Figure5_algorithm_top20.csv')
    fig,axes=panels(height=82,bottom=.27,top=.81,left=.155,gap=.58)
    products=['DSWx','MNDWI','AWEI']
    for ax,metric,n_col,title in zip(axes,['overlap_mean','spearman_mean'],
        ['overlap_event_count','rank_event_count'],['Target selection','Rank agreement']):
        labels=[]
        for i,p in enumerate(products):
            g=sorted([r for r in d if r['product']==p],key=lambda r:float(r['scale_m']))
            assert len(g)==2 and len({r[n_col] for r in g})==1
            ax.plot(col(g,metric),[i,i],color='#A2A8AB',lw=1,zorder=1)
            for scale,color,marker in [(500,BLUE,'o'),(10000,VERMILLION,'s')]:
                row=next(r for r in g if float(r['scale_m'])==scale)
                ax.scatter(float(row[metric]),i,s=30,color=color,marker=marker,zorder=3)
            labels.append(f'{p} (n = {int(float(g[0][n_col]))})')
        ax.set_yticks(range(3),labels);ax.set_ylim(2.6,-.6);ax.set_xlim(0,1);ax.set_xticks(np.arange(0,1.01,.2))
        ax.set_xlabel('Top 20% overlap' if metric=='overlap_mean' else 'Spearman ρ',labelpad=5)
        ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0,pad=8)
        heading(ax,'a' if metric=='overlap_mean' else 'b',title,label_x=-.29)
    h=[Line2D([],[],color=BLUE,marker='o',lw=0,ms=4),Line2D([],[],color=VERMILLION,marker='s',lw=0,ms=4)]
    outside_legend(fig,h,['500 m','10 km'],y=.03)
    finish(fig,'Figure5_Algorithm_sensitivity',[source],'True 20% budget formulation comparison; metric-specific n shown. Metric-specific event counts are shown.')
def figure6(args):
    source,report=INPUT/'utility_macro_summary.csv',INPUT/'utility_experiment_report.json'
    support_source=INPUT/'support_utility_summary.csv'
    meta=json.loads(report.read_text());assert meta['primary_budget']==.2 and meta['bootstrap_repetitions']==10000
    order=['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score']
    rows={r['score']:r for r in read_csv(source) if r['subset']=='blind_primary'};d=[rows[s] for s in order]
    assert np.all(col(d,'event_count')==4)
    sd=sorted([r for r in read_csv(support_source) if r['score']=='agreement_weighted_score'],key=lambda r:float(r['threshold']))
    assert len(sd)==3 and np.all(col(sd,'events')==4) and np.all(col(sd,'total_candidate_counties')==34)
    assert np.allclose(col(sd,'threshold'),[.9,.95,.99])
    assert np.isclose(float(sd[1]['mean_lift']),float(d[3]['event_mean_capture_lift']))
    data_copy(d,'Figure6_utility_top20.csv');data_copy(sd,'Figure6_support_thresholds.csv')
    fig,axes=panels(height=87,bottom=.25,top=.82,left=.19,gap=.65)
    for i,(r,color,marker) in enumerate(zip(d,[BLUE,VERMILLION,GREEN,PURPLE],['o','s','^','D'])):
        y,lo,hi=[float(r[k]) for k in ['event_mean_capture_lift','bootstrap_95_low','bootstrap_95_high']]
        axes[0].errorbar(y,i,xerr=[[y-lo],[hi-y]],color=color,marker=marker,ms=4.3,lw=1,capsize=2.5,zorder=3)
    axes[0].set_yticks(range(4),['S30','L30','Unweighted consensus','AWC']);axes[0].set_ylim(3.65,-.6)
    for i,r in enumerate(sd):
        y,lo,hi=[float(r[k]) for k in ['mean_lift','ci95_low','ci95_high']]
        color,marker=(PURPLE,'D') if float(r['threshold'])==.95 else (GRAY,'o')
        axes[1].errorbar(y,i,xerr=[[y-lo],[hi-y]],color=color,marker=marker,ms=4.3,lw=1,capsize=2.5,zorder=3)
    axes[1].set_yticks(range(3),['90%','95%','99%']);axes[1].set_ylim(2.5,-.5)
    for ax in axes:
        ax.set_xlim(0,3.4);ax.set_xticks([0,1,2,3]);ax.set_xlabel('RMA indemnity capture lift',labelpad=5)
        ax.axvline(1,color='#797979',ls=(0,(4,3)),lw=.75,zorder=0)
        ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0,pad=8)
    heading(axes[0],'a','Priority score at 95% support',label_x=-.54)
    heading(axes[1],'b','AWC by support threshold',label_x=-.22)
    fig.text(.5,.088,'Four events; budget = 20%; whiskers: 95% event bootstrap intervals (10,000 draws).',ha='center',fontsize=8,color=INK)
    fig.text(.5,.036,'Dashed line: random allocation at the same exact county budget.',ha='center',fontsize=8,color=INK)
    finish(fig,'Figure6_External_loss_check',[source,report,support_source],
           'Original four-event 95% support score comparison and 90/95/99% support sensitivity. No new analysis.')
def main():
    for entry in json.loads((INPUT/'input_manifest.json').read_text(encoding='utf-8')):
        assert sha256(INPUT/entry['file'])==entry['sha256'],('Input hash mismatch',entry['file'])
    for n in ARGS.figures:globals()[f'figure{n}'](ARGS)
    # A selected-figure rerun must preserve entries and QA for the other figures.
    manifest_path = OUT/'figure_manifest.json'
    if manifest_path.exists() and set(ARGS.figures) != set(range(1,7)):
        previous = json.loads(manifest_path.read_text(encoding='utf-8'))
        updated = {entry['figure']:entry for entry in MANIFEST}
        combined = [updated.pop(entry['figure'],entry) for entry in previous]
        combined.extend(updated.values())
    else:
        combined = MANIFEST
    manifest_path.write_text(json.dumps(combined,indent=2),encoding='utf-8')
    print('ALL REQUESTED FIGURES PASSED DETERMINISTIC CHECKS',flush=True)
if __name__=='__main__':main()
