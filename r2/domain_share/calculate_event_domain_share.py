"""Compute retained geometric event-domain shares from frozen support counts."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
EVENTS = [
    'N2023_179508_MINNESOTA',
    'N2023_179829_WISCONSIN',
    'N2023_180114_SOUTHDAKOTA',
    'N2024_191762_IOWA',
    'N2025_202615_MISSOURI',
]


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--cells', type=Path, default=ROOT.parent / 'inputs' / 'primary_500m_cells.parquet')
    parser.add_argument('--output', type=Path, default=ROOT / 'event_domain_share.csv')
    args = parser.parse_args()

    freeze = json.loads((ROOT / 'noaa_blind_analysis_domain_freeze_report.json').read_text(encoding='utf8'))
    for filename, digest in freeze['sha256'].items():
        assert sha256((ROOT / filename).read_bytes()).hexdigest() == digest, filename

    domains = pd.read_csv(ROOT / 'noaa_blind_analysis_domain_registry.csv').set_index('event_id').loc[EVENTS]
    assert domains.resolution_m.eq(30).all()
    domains = domains[['state', 'domain_area_km2', 'resolution_m']].copy()
    columns = ['event_id', 'eligible_pixel_count', 'strict_common_valid_coverage', 'strict_common_valid_pixel_count']
    cells = pd.read_parquet(args.cells, columns=columns)
    cells = cells.loc[cells.event_id.isin(EVENTS) & cells.eligible_pixel_count.gt(0)]
    accepted = cells.loc[cells.strict_common_valid_coverage.ge(0.95) & cells.strict_common_valid_pixel_count.gt(0)]
    counts = accepted.groupby('event_id').agg(
        accepted_500m_cells=('eligible_pixel_count', 'size'),
        eligible_30m_pixels_in_accepted_cells=('eligible_pixel_count', 'sum'),
        common_valid_eligible_30m_pixels=('strict_common_valid_pixel_count', 'sum'),
    )
    counts = domains.join(counts)
    assert counts.accepted_500m_cells.sum() == 44510
    pixel_area_km2 = counts.resolution_m.pow(2) / 1_000_000
    counts['common_valid_eligible_area_km2'] = counts.common_valid_eligible_30m_pixels * pixel_area_km2
    counts['common_valid_pct_of_geometric_domain'] = 100 * counts.common_valid_eligible_area_km2 / counts.domain_area_km2
    counts['nominal_accepted_cell_area_km2'] = counts.accepted_500m_cells * (500 ** 2 / 1_000_000)
    counts['nominal_accepted_cell_area_pct_of_domain'] = 100 * counts.nominal_accepted_cell_area_km2 / counts.domain_area_km2
    counts.to_csv(args.output, float_format='%.9f')
    print(counts.to_string())


if __name__ == '__main__':
    main()
