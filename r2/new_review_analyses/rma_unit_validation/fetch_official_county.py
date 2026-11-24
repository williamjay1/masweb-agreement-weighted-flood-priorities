from pathlib import Path
import requests,json,time,argparse
ap=argparse.ArgumentParser(description='Download official RMA county crop plan reports without overwriting existing raw files')
ap.add_argument('--output-dir',type=Path,required=True)
a=ap.parse_args(); out=a.output_dir; out.mkdir(parents=True,exist_ok=True); url='https://public-rma.fpac.usda.gov/apps/SummaryOfBusiness/ReportGenerator/GetResultsData'
for year,state in [('2023','27'),('2023','46'),('2024','19'),('2025','29')]:
 p=out/f'sob_{year}_{state}_corn_soy_by_county_plan.json'
 q={'CC':'S','CY':year,'RY':'','SLCY':'False','SLRY':'False','CM':'0041,0081','AIP':'','DT':'','ST':state,'CT':'','IP':'01,02,03','CVL':'','ORD':'CY,ST,CT,CM,IP','page':'1','pageSize':'1000','skip':'0','take':'1000'}
 if not p.exists():
  for i in range(5):
   r=requests.post(url,data=q,timeout=120)
   if r.status_code==200:
    try:j=r.json();break
    except Exception:pass
   print('retry',year,state,i,r.status_code,flush=True);time.sleep(2+i)
  else:raise RuntimeError((year,state))
  p.write_text(json.dumps({'url':url,'request_parameters':q,'response':j},indent=2),encoding='utf8')
 else:j=json.loads(p.read_text(encoding='utf8'))['response']
 assert len(j['Items'])==j['TotalCount'],(year,state,len(j['Items']),j['TotalCount'])
 print(year,state,'rows',len(j['Items']),'units',sorted({x['CommodityReportingLevelType'] for x in j['Items']}),flush=True)
