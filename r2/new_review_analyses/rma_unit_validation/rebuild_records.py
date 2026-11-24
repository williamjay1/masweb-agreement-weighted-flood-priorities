from pathlib import Path
import csv,zipfile,io,argparse
import pandas as pd, numpy as np
ap=argparse.ArgumentParser(description="Reconstruct the RMA records in the archived 95% analysis")
ap.add_argument('--col-dir',type=Path,required=True,help='Directory containing colsom_2023.zip through colsom_2025.zip')
ap.add_argument('--inputs-dir',type=Path,required=True,help='Directory containing archived county scores and outcomes CSVs')
ap.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
a=ap.parse_args(); O=a.output_dir; O.mkdir(parents=True,exist_ok=True); raw=a.col_dir; base=a.inputs_dir
out=pd.read_csv(base/'primary_external_event_county_outcomes_normalized.csv',dtype={'county_fips':str});sel=pd.read_csv(base/'county_scores_and_selections.csv',dtype={'county_fips':str});sel=sel[sel.threshold==.95][['event_id','county_fips']].drop_duplicates();out=out.merge(sel,on=['event_id','county_fips'],validate='one_to_one');assert len(out)==37
fields=['commodity_year','state_code','state','county_code','county','commodity_code','commodity','insurance_plan_code','insurance_plan','coverage_category','stage_code','cause_code','cause','month_of_loss','month_name','year_of_loss','policies_earning_premium','policies_indemnified','net_planted_quantity','net_endorsed_acres','liability','total_premium','producer_paid_premium','subsidy','state_private_subsidy','additional_subsidy','efa_premium_discount','net_determined_quantity','indemnity','loss_ratio']
targets={}
for row in out.itertuples(index=False):
 for month in pd.period_range(row.event_start,row.event_end,freq='M').month:targets.setdefault((int(row.event_year),str(row.county_fips).zfill(5),int(month)),[]).append(row.event_id)
rows=[]
for year in [2023,2024,2025]:
 p=raw/f'colsom_{year}.zip'
 with zipfile.ZipFile(p) as z:
  with z.open(z.namelist()[0]) as h:
   for vals in csv.reader(io.TextIOWrapper(h,encoding='latin-1'),delimiter='|'):
    if len(vals)!=30:continue
    vals=[x.strip() for x in vals];r=dict(zip(fields,vals));key=(int(r['commodity_year']),r['state_code'].zfill(2)+r['county_code'].zfill(3),int(r['month_of_loss']) if r['month_of_loss'].isdigit() else -1)
    if key not in targets or r['commodity'].lower() not in {'corn','soybean','soybeans'} or r['cause_code'] not in {'31','44','51'}:continue
    for event in targets[key]:rows.append({'event_id':event,'county_fips':key[1],**r})
d=pd.DataFrame(rows)
for c in ['net_planted_quantity','indemnity','liability']:d[c]=pd.to_numeric(d[c],errors='raise')
d.to_csv(O/'primary_selected_rma_rows.csv',index=False)
g=d.groupby(['event_id','county_fips'],as_index=False).agg(raw_rows=('commodity','size'),recomputed_planted=('net_planted_quantity','sum'),recomputed_indemnity=('indemnity','sum'),recomputed_liability=('liability','sum'))
v=out.merge(g,on=['event_id','county_fips'],how='left').fillna({'raw_rows':0,'recomputed_planted':0,'recomputed_indemnity':0,'recomputed_liability':0})
for a,b in [('rma_net_planted_quantity','recomputed_planted'),('rma_indemnity_usd','recomputed_indemnity'),('rma_liability_usd','recomputed_liability')]:v[a+'_diff']=v[a]-v[b]
print('raw rows',len(d),'candidate county rows',len(v),'maxdiffs',v[['rma_net_planted_quantity_diff','rma_indemnity_usd_diff','rma_liability_usd_diff']].abs().max().to_dict())
print(d.groupby(['commodity_year','state','commodity_code','commodity','insurance_plan_code','insurance_plan']).agg(rows=('event_id','size'),net_planted=('net_planted_quantity','sum')).to_string())
v.to_csv(O/'county_reconstruction_check.csv',index=False)
d.groupby(['commodity_year','state','commodity_code','commodity','insurance_plan_code','insurance_plan'],as_index=False).agg(rows=('event_id','size'),net_planted=('net_planted_quantity','sum'),indemnity=('indemnity','sum')).to_csv(O/'selected_record_commodity_plan_groups.csv',index=False)
