from pathlib import Path
import requests,hashlib,json,concurrent.futures
out=Path(r'external/data/Geocarto_R2_20261115/raw/ai4g_2023_event_tiles');out.mkdir(parents=True,exist_ok=True)
items=['N45/N45W093/N45W093-post-processing.parquet','N42/N42W099/N42W099-post-processing.parquet','N42/N42W102/N42W102-post-processing.parquet','N45/N45W099/N45W099-post-processing.parquet']
root='https://huggingface.co/datasets/ai-for-good-lab/ai4g-flood-dataset/resolve/main/'
def run(name):
 dst=out/Path(name).name
 if dst.exists(): print('existing',name,dst.stat().st_size,flush=True);return
 tmp=out/(dst.name+'.partial')
 if tmp.exists(): print('partial exists, skipping',name,flush=True);return
 with requests.get(root+name,stream=True,timeout=(30,150)) as r:
  r.raise_for_status();h=hashlib.sha256();n=0
  with tmp.open('xb') as f:
   for chunk in r.iter_content(1024*1024):
    if chunk:f.write(chunk);h.update(chunk);n+=len(chunk)
 tmp.rename(dst);print('DONE',name,n,h.hexdigest(),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for fut in concurrent.futures.as_completed([ex.submit(run,x) for x in items]):
  try:fut.result()
  except Exception as e: print('ERROR',repr(e),flush=True)
