"""Sensitivity to the one selected claim row with a different loss year.

Keep all county ranks, event domains and other RMA values fixed. Remove the
identified $1,935 row from Spink County and re-evaluate 20% capture lift.
This does not establish which event caused any claim.
"""
from pathlib import Path
import csv, io, zipfile
import numpy as np
import pandas as pd

base = Path(__file__).resolve().parent
root = base / 'results'
root.mkdir(exist_ok=True)
archive = base / 'inputs/colsom_2023.zip'
inputs = base / 'inputs'
records = pd.read_csv(inputs / 'county_scores_and_selections.csv', dtype={'county_fips': str})
reference = pd.read_csv(inputs / 'utility_event_metrics.csv')
fields = ['commodity_year','state_code','state','county_code','county','commodity_code','commodity','insurance_plan_code','insurance_plan','coverage_category','stage_code','cause_code','cause','month_of_loss','month_name','year_of_loss','policies_earning_premium','policies_indemnified','net_planted_quantity','net_endorsed_acres','liability','total_premium','producer_paid_premium','subsidy','state_private_subsidy','additional_subsidy','efa_premium_discount','net_determined_quantity','indemnity','loss_ratio']
matches = []
with zipfile.ZipFile(archive) as z:
    with z.open(next(f for f in z.namelist() if not f.endswith('/'))) as raw:
        for values in csv.reader(io.TextIOWrapper(raw, encoding='latin-1'), delimiter='|'):
            if len(values) != len(fields):
                continue
            d = dict(zip(fields, map(str.strip, values)))
            if (d['commodity_year'],d['state'],d['county_code'],d['commodity'].lower(),d['stage_code'],d['cause_code'],d['month_of_loss'],d['year_of_loss']) == ('2023','SD','115','soybeans','PF','31','04','2022') and float(d['indemnity']) == 1935:
                matches.append(d)
assert len(matches) == 1
records = records[np.isclose(records.threshold, 0.95)].copy()
scores = ['s30_water_fraction','l30_water_fraction','consensus_rank','agreement_weighted_score']
def allocation(v):
    a = np.asarray(v, float); t = 0.2 * len(a)
    cutoff = np.sort(a)[::-1][int(np.ceil(t))-1]
    above = a > cutoff; tied = a == cutoff
    return above.astype(float) + tied * ((t - above.sum()) / tied.sum())
rows = []
for event, g in records.groupby('event_id', sort=True):
    y = g.rma_indemnity_usd.fillna(0).to_numpy(float)
    if y.sum() == 0:
        continue
    adjusted = y.copy()
    if event == 'N2023_180114_SOUTHDAKOTA':
        ix = np.flatnonzero(g.county_fips.to_numpy() == '46115')
        assert len(ix) == 1 and adjusted[ix[0]] >= 1935
        adjusted[ix[0]] -= 1935
    for score in scores:
        w = allocation(g[score])
        before = float(w @ y / y.sum() / 0.2)
        after = float(w @ adjusted / adjusted.sum() / 0.2)
        old = reference.loc[np.isclose(reference.threshold, .95) & reference.event_id.eq(event) & reference.score.eq(score), 'lift']
        assert len(old) == 1 and np.isclose(before, old.iloc[0], rtol=0, atol=1e-10)
        rows.append({'event_id':event,'score':score,'original_lift':before,'exclude_other_loss_year_lift':after,'difference':after-before})
df = pd.DataFrame(rows)
assert df.event_id.nunique() == 4 and len(df) == 16
df.to_csv(root/'rma_loss_year_event_sensitivity.csv',index=False)
summary = df.groupby('score',as_index=False)[['original_lift','exclude_other_loss_year_lift','difference']].mean()
summary.to_csv(root/'rma_loss_year_summary.csv',index=False)
print(df[df.event_id.str.contains('SOUTHDAKOTA')].to_string(index=False))
print(summary.to_string(index=False))
