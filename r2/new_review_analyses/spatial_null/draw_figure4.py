from pathlib import Path
import sys,os,json
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'mpl_cache')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from figstyle import apply_house_style,audit,mm
import numpy as np,pandas as pd
plt=apply_house_style()
plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
here=Path(__file__).resolve().parent
summ=pd.read_csv(here/'random_placement_summary.csv')
src=here.parents[1]/'inputs/new_review_archives/Figure4_mechanism_summary.csv'
obs=pd.read_csv(src)
out=here/'figures';out.mkdir(exist_ok=True)
fig,axes=plt.subplots(1,2,figsize=(mm(183),mm(82)))
fig.subplots_adjust(left=.095,right=.98,top=.84,bottom=.28,wspace=.30)
cols={'s30':'#0072B2','l30':'#D55E00'}
for j,(ax,metric,title) in enumerate(zip(axes,['rank_persistence','sd_ratio'],['Rank persistence','Score dispersion'])):
 for p,marker in [('s30','o'),('l30','s')]:
  v=summ[(summ.metric==metric)&(summ['product']==p)].sort_values('scale_km')
  assert len(v)==6 and len(obs)==7
  assert np.allclose(v.observed_mean.to_numpy(),obs.loc[obs.scale_km>0.5,p+'_'+metric+'_mean'].to_numpy(),atol=1e-5)
  ax.plot(np.arange(7),obs[p+'_'+metric+'_mean'],color=cols[p],marker=marker,ms=3.2,lw=1.35,label=p.upper()+' observed',zorder=3)
  ax.plot(np.arange(7),np.r_[1,v.random_median_mean],color=cols[p],ls=(0,(3,2)),lw=1.25,label=p.upper()+' randomized',zorder=2)
 ax.set_xticks(range(7),['0.5','1','2','5','10','20','30'])
 ax.set_xlabel('Grid size (km)')
 ax.set_ylim(0,1.12);ax.set_yticks([0,.25,.5,.75,1])
 ax.grid(axis='y',color='#dedede',lw=.5)
 ax.text(-.15,1.045,'ab'[j],transform=ax.transAxes,fontweight='bold',fontsize=10,va='bottom')
 ax.set_title(title,loc='left',fontsize=8.5,fontweight='bold',pad=8)
axes[0].set_ylabel('Spearman rank correlation')
axes[1].set_ylabel('SD ratio relative to 500 m')
handles,labels=axes[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='lower center',ncol=4,frameon=False,bbox_to_anchor=(.5,.06),columnspacing=1.5,handlelength=2)
report=audit(fig)
(here/'figure4_audit.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf8')
for ext in ['pdf','svg']:fig.savefig(out/('Figure4_Mechanism_diagnostics.'+ext))
fig.savefig(out/'Figure4_Mechanism_diagnostics.tif',dpi=1200,pil_kwargs={'compression':'tiff_lzw'})
fig.savefig(out/'Figure4_preview.png',dpi=180)
print(json.dumps(report,indent=2,default=str))

