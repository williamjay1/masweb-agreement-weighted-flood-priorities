"""Event totals and binary disagreement on the archived strict common domain.

Counts refer to nominal 30 m common-valid eligible pixels contained in accepted
500 m cells. They are mapped-class agreements, not accuracy against truth.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

base = Path(__file__).resolve().parent
source = base / 'inputs' / 'primary_500m_cells.parquet'
events = ['N2023_179508_MINNESOTA', 'N2023_179829_WISCONSIN',
          'N2023_180114_SOUTHDAKOTA', 'N2024_191762_IOWA',
          'N2025_202615_MISSOURI']
cols = ['event_id', 'strict_common_valid_coverage', 'strict_common_valid_pixel_count',
        'strict_s30_water_pixel_count', 'strict_l30_water_pixel_count',
        'strict_intersection_pixel_count', 'strict_union_pixel_count']
data = pd.read_parquet(source, columns=cols)
data = data[data.event_id.isin(events) & data.strict_common_valid_coverage.ge(.95)
            & data.strict_common_valid_pixel_count.gt(0)].copy()
assert len(data) == 44510
s, l = data.strict_s30_water_pixel_count, data.strict_l30_water_pixel_count
i, u, n = data.strict_intersection_pixel_count, data.strict_union_pixel_count, data.strict_common_valid_pixel_count
assert ((s >= 0) & (l >= 0) & (i >= 0) & (u <= n) & (i <= s) & (i <= l) & (u == s + l - i)).all()
counts = data.groupby('event_id', sort=False).agg(
    accepted_cells=('event_id', 'size'), valid_pixels=('strict_common_valid_pixel_count', 'sum'),
    s30_water=('strict_s30_water_pixel_count', 'sum'), l30_water=('strict_l30_water_pixel_count', 'sum'),
    both_water=('strict_intersection_pixel_count', 'sum'), either_water=('strict_union_pixel_count', 'sum'))
counts = counts.loc[events].copy()
counts['jaccard'] = counts.both_water.div(counts.either_water.where(counts.either_water.gt(0)))
counts['quantity_disagreement'] = (counts.s30_water - counts.l30_water).abs() / counts.valid_pixels
counts['allocation_disagreement'] = 2 * (counts[['s30_water', 'l30_water']].min(axis=1) - counts.both_water) / counts.valid_pixels
counts['total_disagreement'] = (counts.either_water - counts.both_water) / counts.valid_pixels
assert np.allclose(counts.quantity_disagreement + counts.allocation_disagreement, counts.total_disagreement, atol=1e-14)
assert counts.accepted_cells.tolist() == [12643, 221, 2628, 28456, 562]
out=base/'results'; out.mkdir(exist_ok=True)
counts.to_csv(out/'event_water_and_disagreement.csv', float_format='%.12g')
manifest = {'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'domain': 'five primary events, strict common-valid coverage >= 0.95, strict common valid count > 0',
            'accepted_cells': int(len(data)),
            'formula': 'Q=abs(S-L)/N; A=2*(min(S,L)-I)/N; total=(U-I)/N=Q+A; J=I/U',
            'limitations': 'Descriptive pixel-count comparison for accepted cells only. Shared algorithm lineage and class errors mean this is not accuracy or external validation.'}
(out/'event_water_and_disagreement_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(counts.to_string())
