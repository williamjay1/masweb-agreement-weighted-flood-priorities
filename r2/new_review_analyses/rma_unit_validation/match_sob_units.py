from pathlib import Path
import pandas as pd,json,argparse
ap=argparse.ArgumentParser(description="Map archived COL rows to official county-crop-plan reporting quantity types")
ap.add_argument('--sob-dir',type=Path,required=True,help='Directory containing the official SOB report JSONs')
ap.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent,help='Directory with primary_selected_rma_rows.csv')
a=ap.parse_args(); O=a.output_dir; p=a.sob_dir
d=pd.read_csv(O/'primary_selected_rma_rows.csv',dtype={'commodity_year':str,'county_fips':str,'commodity_code':str,'insurance_plan_code':str});rows=[]
for f in sorted(p.glob('sob_*_by_county_plan.json')):
 j=json.loads(f.read_text(encoding='utf8'))
 for x in j['response']['Items']:rows.append({'commodity_year':x['CommodityYear'],'county_fips':x['LocationStateCode']+x['LocationCountyCode'],'commodity_code':x['CommodityCode'],'insurance_plan_code':x['InsurancePlanCode'],'insurance_plan_sob':x['InsurancePlanAbbreviation'],'unit':x['CommodityReportingLevelType'],'provider_report':f.name})
s=pd.DataFrame(rows);keys=['commodity_year','county_fips','commodity_code','insurance_plan_code'];assert not s.duplicated(keys).any()
x=d.merge(s,on=keys,how='left',validate='many_to_one');print('record matches',len(x),x.unit.notna().sum(),'units',x.unit.value_counts(dropna=False).to_dict());print('unmatched:',x.loc[x.unit.isna(),keys+['commodity','insurance_plan']].drop_duplicates().to_string(index=False));print('unique mapped',len(x[keys].drop_duplicates()))
x.to_csv(O/'rma_record_to_official_unit.csv',index=False);x[keys+['insurance_plan','insurance_plan_sob','unit','provider_report']].drop_duplicates().to_csv(O/'official_quantity_type_by_event_county_plan.csv',index=False)
