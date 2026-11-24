from pathlib import Path
import pandas as pd,numpy as np,hashlib,json,shutil
out=Path(__file__).resolve().parent
p=out/'inputs/archived_common_support_report.json'
report=json.loads(p.read_text(encoding='utf8'))
data=out/'inputs/hls_index_500m_cells.parquet'
assert hashlib.sha256(data.read_bytes()).hexdigest()==report['output_sha256']['hls_index_500m_cells.parquet']
ledger=pd.read_csv(out/'inputs/otsu_support_ledger_stripped.csv')
for x in ledger.itertuples():
    p=out/'inputs/otsu_cells'/f'{x.event_id}_hls_index_500m_cells.parquet'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==x.sha256
audit=pd.read_csv(out/'inputs/hls_item_resolution_audit_stripped.csv')
ids=['N2023_179508_MINNESOTA','N2023_179829_WISCONSIN','N2023_180114_SOUTHDAKOTA','N2024_191762_IOWA','N2025_202615_MISSOURI']
audit=audit[audit.event_id.isin(ids)].copy()
cols=['event_id','pair_id','sensor_family','sensor','tile','acquisition_datetime_utc','expected_item_id','resolved_item_id','resolution_method','resolution_status','item_json_sha256']
audit[cols].to_csv(out/'results/hls_item_resolution_audit_stripped.csv',index=False)
for ev in ['N2023_179829_WISCONSIN','N2024_191762_IOWA','N2025_202615_MISSOURI']:
 x=audit[audit.event_id.eq(ev)]
 assert x.resolution_status.eq('resolved').all()
 assert x.expected_item_id.eq(x.resolved_item_id).all()
ref=pd.read_csv(out/'inputs/primary_tie_and_support_sensitivity.csv')
res=pd.read_csv(out/'results/primary_common_four_chain_event_metrics.csv')
ref=ref[(ref.budget==.2)&(ref.minimum_eligible_pixels==1)]
res=res[(res['product']=='dswx')&res.event_id.isin(['N2023_179829_WISCONSIN','N2024_191762_IOWA','N2025_202615_MISSOURI'])].copy()
res['scale_km']=res.scale_m/1000
j=res.merge(ref,on=['event_id','scale_km'],suffixes=('_new','_primary'),validate='one_to_one')
assert len(j)==21 and (j.n_units==j.units).all()
j['rho_abs_difference']=(j.spearman-j.rho).abs()
j['coordinate_abs_difference']=(j.coordinate_topk_overlap-j.overlap_coordinate).abs()
j['random_tie_abs_difference']=(j.independent_cutoff_ties_expected_overlap-j.overlap_expected_independent_random_ties).abs()
assert j.coordinate_abs_difference.max()<1e-10 and j.random_tie_abs_difference.max()<1e-10
assert j.rho_abs_difference.max()<1e-4
cols=['event_id','scale_km','n_units','rho_abs_difference','coordinate_abs_difference','random_tie_abs_difference']
j[cols].to_csv(out/'results/primary_dswx_crosscheck.csv',index=False)
lineage=pd.read_csv(out/'inputs/hls_lineage_archived_metrics.csv')
lineage=lineage[lineage.budget.eq(.2)][['event_id','scale_km','n_cells','k','spearman','kendall','topk_overlap','target_replacement']]
lineage.to_csv(out/'results/hls_lineage_per_event_budget20.csv',index=False,float_format='%.12g')
print('verified SHA256 and resolution; 21 DSWx event-scale matched; max rho difference',j.rho_abs_difference.max())

