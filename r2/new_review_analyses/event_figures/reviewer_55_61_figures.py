from pathlib import Path
import os,sys,json,hashlib
ROOT=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'mpl_cache')
sys.path.insert(0,str(ROOT))
from figstyle import apply_house_style,audit,mm
import numpy as np,pandas as pd
from matplotlib.lines import Line2D
plt=apply_house_style()
plt.rcParams.update({'font.family':'Arial','font.size':7.2,'axes.labelsize':7.2,'xtick.labelsize':6.2,'ytick.labelsize':6.2,'legend.fontsize':7,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65})
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
def export(fig,stem):
 report=audit(fig);(OUT/(stem+'_audit.json')).write_text(json.dumps(report,indent=2,default=str),encoding='utf8')
 for ext in ['pdf','svg']:fig.savefig(OUT/(stem+'.'+ext))
 fig.savefig(OUT/(stem+'.tif'),dpi=1200,pil_kwargs={'compression':'tiff_lzw'})
 fig.savefig(OUT/(stem+'_preview.png'),dpi=160)
 plt.close(fig)
 print(stem,report['ok'])

# Five individual events, with the same eligible units and 20% decision budget.
d=pd.read_csv(ROOT/'inputs/historical_hls_sar_per_event_metrics.csv')
d=d[np.isclose(d.budget,.2)].copy(); assert len(d)==35
names=['Minnesota','Wisconsin','South Dakota','Iowa','Missouri'];suf=['MINNESOTA','WISCONSIN','SOUTHDAKOTA','IOWA','MISSOURI']
fig,axes=plt.subplots(5,2,figsize=(mm(183),mm(185)),sharex=False,sharey='col')
fig.subplots_adjust(left=.095,right=.985,top=.95,bottom=.075,wspace=.24,hspace=.55)
scales=[.5,1,2,5,10,20,30]
for row,(name,suffix) in enumerate(zip(names,suf)):
 g=d[d.event_id.str.endswith(suffix)].sort_values('scale_km'); assert np.allclose(g.scale_km,scales)
 for col,(key,color) in enumerate([('topk_overlap','#0072B2'),('spearman','#D55E00')]):
  ax=axes[row,col];x=np.arange(7);y=g[key].to_numpy();n=g.n_cells.to_numpy();
  ax.plot(x,y,color=color,lw=1.1,zorder=2)
  ax.scatter(x[n>=20],y[n>=20],s=17,color=color,edgecolors=color,zorder=3)
  ax.scatter(x[n<20],y[n<20],s=18,facecolors='white',edgecolors=color,linewidths=.9,zorder=4)
  ax.grid(axis='y',color='#e0e0e0',lw=.45,zorder=0)
  ax.set_xticks(x,[f'{sc:g}\n{int(count):,}' for sc,count in zip(scales,n)],fontsize=5.6)
  if col==0:ax.set_ylim(-.06,1.07);ax.set_yticks([0,.5,1]);ax.set_ylabel(name+'\nOverlap')
  else:ax.set_ylim(-.47,1.07);ax.set_yticks([-.4,0,.4,.8]);ax.set_ylabel('Spearman $\\rho$')
  ax.tick_params(axis='x',length=2,pad=1)
axes[0,0].set_title('a  Top 20% overlap',loc='left',fontweight='bold',fontsize=8.5,pad=8)
axes[0,1].set_title('b  Rank correlation',loc='left',fontweight='bold',fontsize=8.5,pad=8)
fig.text(.5,.026,'Grid size (km)  /  eligible units (n)     Open markers: n < 20',ha='center',va='center',fontsize=7)
d[['event_id','scale_km','n_cells','k','topk_overlap','spearman']].sort_values(['event_id','scale_km']).to_csv(ROOT/'results/figure3_small_multiples_data.csv',index=False)
export(fig,'Figure3_Event_heterogeneity')

# Comparator capture and lift curves for the four events with positive RMA outcomes.
d=pd.read_csv(ROOT/'inputs/county_ablations_event_budget.csv')
keys=['agreement_weighted_score','s30_water_fraction','l30_water_fraction','consensus_rank']
d=d[np.isclose(d.threshold,.95)&d.score.isin(keys)&d.lift.notna()].copy()
assert d.event_id.nunique()==4 and len(d)==4*4*10
assert d.groupby(['budget','score']).event_id.nunique().eq(4).all()
summary=d.groupby(['budget','score'],as_index=False).agg(events=('event_id','nunique'),capture=('capture','mean'),lift=('lift','mean'))
assert np.allclose(summary.capture,summary['budget']*summary.lift)
summary.to_csv(ROOT/'results/score_budget_curve_summary.csv',index=False)
d.to_csv(ROOT/'results/score_budget_curve_by_event.csv',index=False)
styles={'agreement_weighted_score':('AWC','#0072B2','o'), 's30_water_fraction':('S30','#D55E00','s'),'l30_water_fraction':('L30','#009E73','^'),'consensus_rank':('Consensus','#7B3294','D')}
fig,axes=plt.subplots(1,2,figsize=(mm(183),mm(88)))
fig.subplots_adjust(left=.09,right=.985,top=.84,bottom=.28,wspace=.30)
for j,(ax,metric,title) in enumerate(zip(axes,['capture','lift'],['Indemnity captured','Capture lift'])):
 for key in keys:
  label,color,marker=styles[key];g=summary[summary.score==key].sort_values('budget')
  ax.plot(100*g.budget,g[metric],color=color,marker=marker,markersize=3.2,lw=1.25,label=label)
 if metric=='capture':ax.plot([5,50],[.05,.5],color='#666',ls=(0,(3,2)),lw=.9,label='Uniform selection')
 else:ax.axhline(1,color='#666',ls=(0,(3,2)),lw=.9,label='Uniform selection')
 ax.set_xlim(4,51);ax.set_xticks([5,10,20,30,40,50]);ax.set_xlabel('County selection budget (%)')
 ax.grid(axis='y',color='#e0e0e0',lw=.45);ax.set_title('ab'[j]+'  '+title,loc='left',fontweight='bold',fontsize=8.5,pad=8)
axes[0].set_ylabel('Mean fraction of indemnity captured');axes[0].set_ylim(0,.85)
axes[1].set_ylabel('Mean lift over uniform selection');axes[1].set_ylim(0,3.1)
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=5,frameon=False,bbox_to_anchor=(.5,.05),columnspacing=1.3,handlelength=1.5)
export(fig,'FigureA2_Comparator_budget_curves')
manifest={'basis':'post hoc summaries from frozen derived inputs, four primary events with positive indemnity; small multiples are five primary events', 'inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'inputs').glob('*.csv')},'outputs':['figure3_small_multiples_data.csv','score_budget_curve_summary.csv','score_budget_curve_by_event.csv'],'limitations':['not independent accuracy validation','curves have four events with equal event weights','coordinate tie convention retained','county score comparisons descriptive']}
(ROOT/'results/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
