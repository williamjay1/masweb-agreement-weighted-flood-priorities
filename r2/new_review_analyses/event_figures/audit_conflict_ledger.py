from pathlib import Path
import pandas as pd
p=Path(__file__).resolve().parent
d=pd.read_csv(p/'inputs/primary_conflicts_ledger_subset.csv'); assert len(d)==10
d['expanded_conflict_percent']=100*d.expanded_conflict_pixels/d.eligible_pixels
d.to_csv(p/'results/primary_conflicts_rates.csv',index=False)
print(d.to_string(index=False))
