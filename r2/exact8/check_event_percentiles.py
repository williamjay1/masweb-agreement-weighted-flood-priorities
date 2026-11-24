"""Recheck the repeated limits in the event-bootstrap calculation."""

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from itertools import combinations_with_replacement
from pathlib import Path


def exact_event_percentiles(event_captures):
    """Apply the linear percentile rule to the full ordered resample distribution."""
    n = len(event_captures)
    ordered_draws = n**n
    weighted_values = []
    for indices in combinations_with_replacement(range(n), n):
        # Each unordered sample represents its multinomial number of ordered draws.
        weight = math.factorial(n) // math.prod(
            math.factorial(count) for count in Counter(indices).values()
        )
        value = math.fsum(event_captures[i] for i in indices) / n
        weighted_values.append((value, weight))
    weighted_values.sort()
    assert sum(weight for _, weight in weighted_values) == ordered_draws

    def order_value(index):
        for value, weight in weighted_values:
            if index < weight:
                return value
            index -= weight
        raise IndexError('Order statistic exceeds the resampling distribution')

    def quantile(probability):
        position = (ordered_draws - 1) * probability
        lower = math.floor(position)
        upper = math.ceil(position)
        left = order_value(lower)
        return left + (position - lower) * (order_value(upper) - left)

    low, high = quantile(0.025), quantile(0.975)
    return {
        'events': n,
        'ordered_event_resamples': ordered_draws,
        'unordered_multisets': len(weighted_values),
        'mean_capture': math.fsum(event_captures) / n,
        'capture_percentile_2_5_to_97_5': [low, high],
        'lift_percentile_2_5_to_97_5': [low / 0.20, high / 0.20],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default_supplement = Path(__file__).resolve().parents[1]
    parser.add_argument('--supplement', type=Path, default=default_supplement)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('event_percentile_results.json'))
    args = parser.parse_args()

    transport_path = Path('new_review_analyses/methods_analysis/eight_event_rma_all_comparators_event.csv')
    primary_path = Path('inputs/utility_event_metrics.csv')
    archive_path = Path('new_review_analyses/methods_analysis/capture_repeated_endpoint_enumeration.csv')

    sets = defaultdict(dict)
    with (args.supplement / transport_path).open(encoding='utf-8-sig', newline='') as source:
        for row in csv.DictReader(source):
            assert row['event_id'] not in sets[row['score']]
            sets[row['score']][row['event_id']] = float(row['capture_lift_over_random']) * 0.20
    assert len(sets) == 4 and all(len(values) == 8 for values in sets.values())
    transport = {score: exact_event_percentiles(list(positions.values())) for score, positions in sets.items()}

    sets = defaultdict(dict)
    with (args.supplement / primary_path).open(encoding='utf-8-sig', newline='') as source:
        for row in csv.DictReader(source):
            if float(row['threshold']) == 0.95 and row['estimable'] == 'True':
                assert row['event_id'] not in sets[row['score']]
                sets[row['score']][row['event_id']] = float(row['capture'])
    assert len(sets) == 4 and all(len(values) == 4 for values in sets.values())
    primary = {score: exact_event_percentiles(list(positions.values())) for score, positions in sets.items()}
    with (args.supplement / archive_path).open(encoding='utf-8-sig', newline='') as source:
        for row in csv.DictReader(source):
            exact = primary[row['score']]['capture_percentile_2_5_to_97_5'][0]
            assert math.isclose(exact, float(row['percentile_2_5']), rel_tol=0, abs_tol=1e-14)

    report = {
        'budget_fraction': 0.20,
        'quantile_definition': 'The exact discrete distribution includes every ordered resample. The quantile linearly interpolates between the ordered values at floor and ceil of p*(N-1), using zero-based ranks.',
        'source_sha256': {
            path.as_posix(): hashlib.sha256((args.supplement / path).read_bytes()).hexdigest()
            for path in [transport_path, primary_path, archive_path]
        },
        'primary_four_events_exact': primary,
        'transport_eight_events_exact': transport,
        'transport_awc_historical_table_values': {
            'capture': 0.326, 'capture_percentile_range': [0.164, 0.489],
            'lift': 1.631, 'lift_percentile_range': [0.822, 2.446],
            'note': 'Rounded values displayed by the historical finite Monte Carlo calculation. The original draw sequence is unavailable.'
        },
        'interpretation': 'The same rounded lower capture value in the historical primary comparator and transport AWC rows does not persist in the exact discrete calculation. These calculations are descriptive and do not establish independent events.'
    }
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {args.output.name}; verified the three archived primary lower endpoints.')


if __name__ == '__main__':
    main()
