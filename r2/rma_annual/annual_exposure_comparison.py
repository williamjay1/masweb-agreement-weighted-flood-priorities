"""Compare event indemnity allocations ranked by annual USDA RMA exposure.

The annual Summary of Business queries include corn and soybean for plans
01, 02 and 03. No matched event losses are used to construct exposure scores.
"""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
BUDGET = 0.20
SCORES = ['agreement_weighted_score', 'annual_reported_acres', 'annual_reported_liability_usd']


def selection_weights(score):
    """Follow the original fractional allocation rule, sharing cutoff ties."""
    score = np.asarray(score, dtype=float)
    allocation = BUDGET * len(score)
    cutoff = np.sort(score)[::-1][int(np.ceil(allocation)) - 1]
    above = score > cutoff
    tied = score == cutoff
    weights = above.astype(float)
    weights[tied] = (allocation - above.sum()) / tied.sum()
    assert np.isclose(weights.sum(), allocation)
    return weights


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--supplement', type=Path, default=HERE.parent)
    args = parser.parse_args()
    scores_file = args.supplement / 'inputs/county_scores_and_selections.csv'
    sources = args.supplement / 'new_review_analyses/rma_unit_validation/provider_snapshots'

    source_records = []
    source_metadata = []
    for path in sorted(sources.glob('sob_*_corn_soy_by_county_plan.json')):
        source = json.loads(path.read_text(encoding='utf8'))
        response = source['response']
        assert len(response['Items']) == response['TotalCount']
        source_metadata.append({'file': path.name, 'request': source['request_parameters'], 'rows': response['TotalCount'], 'sha256': sha256(path.read_bytes()).hexdigest()})
        source_records.extend(response['Items'])

    annual = pd.DataFrame(source_records)
    unique_keys = ['CommodityYear', 'LocationStateCode', 'LocationCountyCode', 'CommodityCode', 'InsurancePlanCode']
    assert len(annual) == 1663
    assert not annual.duplicated(unique_keys).any()
    assert set(annual.CommodityCode) == {'0041', '0081'}
    assert set(annual.InsurancePlanCode) == {'01', '02', '03'}
    assert annual.CommodityReportingLevelType.eq('Acres').all()
    annual['county_fips'] = annual.LocationStateCode + annual.LocationCountyCode
    annual['event_year'] = annual.CommodityYear.astype(int)
    exposure = annual.groupby(['county_fips', 'event_year'], as_index=False).agg(
        annual_reported_acres=('CommodityReportingLevelAmount', 'sum'),
        annual_reported_liability_usd=('LiabilityAmount', 'sum'),
        annual_reporting_rows=('InsurancePlanCode', 'size'),
    )

    counties = pd.read_csv(scores_file, dtype={'county_fips': str})
    counties = counties.loc[np.isclose(counties.threshold, .95)].copy()
    counties = counties.loc[counties.groupby('event_id').rma_indemnity_usd.transform('sum').gt(0)].copy()
    counties['event_year'] = counties.event_id.str[1:5].astype(int)
    counties = counties.merge(exposure, on=['county_fips', 'event_year'], how='left', validate='one_to_one')
    counties['annual_record_reported'] = counties.annual_reporting_rows.notna()
    assert len(counties) == 34
    absent = counties.loc[~counties.annual_record_reported]
    assert absent.rma_indemnity_usd.eq(0).all()
    assert len(absent) == 4
    assert counties.loc[counties.annual_record_reported, SCORES[1:]].gt(0).all().all()

    event_results = []
    county_results = []
    full_set = 'fixed_county_set_missing_annual_last'
    for scenario, table in [(full_set, counties), ('reported_annual_counties_only', counties.loc[counties.annual_record_reported])]:
        for event, group in table.groupby('event_id', sort=True):
            total = group.rma_indemnity_usd.sum()
            for score in SCORES:
                # An absent official result is ranked below a reported positive value.
                values = group[score].fillna(-1.0)
                weights = selection_weights(values)
                if score == SCORES[0] and scenario == full_set:
                    assert np.allclose(weights, group.agreement_weighted_score_selection_weight)
                if score != SCORES[0]:
                    assert (weights[values < 0] == 0).all()
                selected_amount = float(weights @ group.rma_indemnity_usd)
                event_results.append({
                    'scenario': scenario, 'event_id': event, 'score': score,
                    'candidate_count': len(group), 'annual_reporting_count': int(group.annual_record_reported.sum()),
                    'budget_county_equivalents': BUDGET * len(group), 'event_indemnity_usd': total,
                    'selected_indemnity_usd': selected_amount, 'capture': selected_amount / total,
                    'lift': selected_amount / total / BUDGET,
                })
                county_results.append(group[['event_id', 'county_fips', 'county_name', 'rma_indemnity_usd', 'annual_record_reported', *SCORES]].assign(scenario=scenario, score=score, selection_weight=weights))

    results = pd.DataFrame(event_results)
    summary = results.groupby(['scenario', 'score'], as_index=False).agg(
        n_events=('event_id', 'size'), mean_lift=('lift', 'mean'), min_lift=('lift', 'min'), max_lift=('lift', 'max'),
    )
    results.to_csv(HERE / 'annual_exposure_event.csv', index=False)
    summary.to_csv(HERE / 'annual_exposure_summary.csv', index=False)
    pd.concat(county_results).to_csv(HERE / 'annual_exposure_county_selections.csv', index=False)
    manifest = {
        'source_snapshots': source_metadata,
        'frozen_scores_hash': sha256(scores_file.read_bytes()).hexdigest(),
        'unreported_county_fips': absent.county_fips.tolist(),
        'reference': 'capture divided by 0.20 for each event, then averaged across four events',
        'budget': BUDGET,
    }
    (HERE / 'annual_exposure_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')
    print(results.to_string(index=False))
    print(summary.to_string(index=False))


if __name__ == '__main__':
    main()
