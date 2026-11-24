from pathlib import Path
import os
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'figures'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.6,'xtick.major.width':.6,'ytick.major.width':.6,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white'})
names=['Minnesota','Wisconsin','South Dakota','Iowa','Missouri']
suffixes=['MINNESOTA','WISCONSIN','SOUTHDAKOTA','IOWA','MISSOURI']
colors=['#0072B2','#D55E00','#009E73','#7B3294','#B07B00']
markers=['o','s','^','D','v']
def label(ax,s,title):
    ax.text(-.13,1.05,s,transform=ax.transAxes,fontweight='bold',fontsize=10,va='bottom')
    ax.set_title(title,loc='left',fontsize=8.5,fontweight='bold',pad=8)
def save(fig,stem):
    for fmt in ('pdf','svg'):
        fig.savefig(OUT/f'{stem}.{fmt}')
    fig.savefig(OUT/f'{stem}.png',dpi=180)
    fig.savefig(OUT/f'{stem}.tif',dpi=1200,pil_kwargs={'compression':'tiff_lzw'})
    plt.close(fig)

def fig2():
    d=pd.read_csv(ROOT/'tie_and_support_sensitivity.csv')
    d=d[(d.minimum_eligible_pixels==1)&(np.isclose(d.budget,.20))&(d.scale_km<=10)]
    scales=np.array([.5,1,2,5,10]); assert len(d)==25
    fig,axes=plt.subplots(1,2,figsize=(183/25.4,90/25.4),sharey=True)
    fig.subplots_adjust(left=.09,right=.98,top=.84,bottom=.29,wspace=.16)
    keys=['overlap_coordinate','overlap_expected_independent_random_ties']
    for j,(ax,key,title) in enumerate(zip(axes,keys,['Coordinate ordered ties','Independent random ties'])):
        for n,c,m,suf in zip(names,colors,markers,suffixes):
            q=d[d.event_id.str.endswith(suf)].sort_values('scale_km'); assert np.allclose(q.scale_km,scales)
            ax.plot(np.arange(5),q[key],color=c,marker=m,markersize=3,lw=.95,alpha=.83)
        avg=d.groupby('scale_km')[key].mean().reindex(scales)
        ax.plot(np.arange(5),avg,color='#1b1b1b',marker='o',markersize=3.5,lw=2,zorder=5)
        ax.set_xticks(range(5),['0.5','1','2','5','10']); ax.set_xlabel('Grid size (km)')
        ax.set_ylim(-.03,1.03); ax.set_yticks([0,.2,.4,.6,.8,1]); ax.grid(axis='y',color='#d9d9d9',lw=.45,zorder=0)
        ax.axhline(.2, color='#666666', linestyle=(0,(4,2)), linewidth=.85, zorder=1)
        label(ax,'ab'[j],title)
    axes[0].set_ylabel('Top 20% overlap')
    handles=[Line2D([0],[0],color=c,marker=m,lw=1,markersize=3,label=n) for n,c,m in zip(names,colors,markers)]
    handles += [Line2D([0],[0],color='#1b1b1b',marker='o',lw=2,markersize=3,label='Event mean'), Line2D([0],[0],color='#666666',linestyle=(0,(4,2)),lw=.85,label='Nominal 0.20')]
    fig.legend(handles=handles,loc='lower center',ncol=4,frameon=False,fontsize=7,columnspacing=1.6,handlelength=1.8,bbox_to_anchor=(.5,.035))
    save(fig,'Figure2_Scale_response')


if __name__ == '__main__':
    fig2()
