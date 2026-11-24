from pathlib import Path
import requests,json,hashlib,time,pandas as pd
out=Path('external/data/Geocarto_R2_20261115/raw/rma_units');url='https://public-rma.fpac.usda.gov/apps/SummaryOfBusiness/ReportGenerator/GetResultsData';groups=[('2023','27'),('2023','46'),('2024','19'),('2025','29')]
for year,state in groups:
 p=out/f'sob_{year}_{state}_corn_soy_by_plan.json'
 q={'CC':'S','CY':year,'RY':'','SLCY':'False','SLRY':'False','CM':'0041,0081','AIP':'','DT':'','ST':state,'CT':'','IP':'','CVL':'','ORD':'CY,ST,CM,IP','page':'1','pageSize':'100','skip':'0','take':'100'}
 if p.exists(): print('using saved',p.name);j=json.loads(p.read_text(encoding='utf8'))
 else:
  for attempt in range(4):
   r=requests.post(url,data=q,timeout=90)
   if r.status_code==200:
    try:j=r.json();break
    except Exception:pass
   print('retry',year,state,attempt,r.status_code,flush=True);time.sleep(2+attempt)
  else:raise RuntimeError((year,state,r.status_code,r.text[:500]))
  p.write_text(json.dumps({'url':url,'request_parameters':q,'response':j},indent=2),encoding='utf8'); j=json.loads(p.read_text(encoding='utf8'))
 data=j['response']['Items'];print(year,state,'rows',len(data),'reported_total',j['response']['TotalCount'],flush=True)
 for x in data:print(x['CommodityYear'],x['LocationStateCode'],x['CommodityCode'],x['InsurancePlanCode'],x['InsurancePlanAbbreviation'],x['CommodityReportingLevelType'],flush=True)
