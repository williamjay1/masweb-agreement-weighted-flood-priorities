"""Recheck 500 m to 10 km changes with the same events at both scales."""

import csv
from pathlib import Path
from statistics import mean


HERE = Path(__file__).resolve().parent
SUPPLEMENT = HERE.parent
SOURCE = (
    SUPPLEMENT / "new_review_analyses/methods_analysis"
    / "primary_all_scales_event_metrics.csv"
)
with SOURCE.open(newline="", encoding="utf8") as stream:
    records = list(csv.DictReader(stream))

by_scale = {
    scale: {r["event_id"]: r for r in records if float(r["scale_km"]) == scale}
    for scale in (0.5, 10.0)
}
events = sorted(by_scale[0.5])
assert events == sorted(by_scale[10.0]) and len(events) == 5
results = []


def compare(name, chosen, collapse_april=False):
    row = {"comparison": name, "events": len(chosen)}
    row["event_ids"] = "|".join(chosen)
    row["groups"] = 3 if collapse_april else len(chosen)
    for metric in ("overlap", "spearman", "kendall_tau_b"):
        for scale, suffix in ((0.5, "500m"), (10.0, "10km")):
            values = {e: float(by_scale[scale][e][metric]) for e in chosen}
            if collapse_april:
                april = [v for e, v in values.items() if e.startswith("N2023_")]
                later = [v for e, v in values.items() if not e.startswith("N2023_")]
                assert len(april) == 3 and len(later) == 2
                summary = mean([mean(april), *later])
            else:
                summary = mean(values.values())
            row[f"{metric}_{suffix}"] = summary
        row[f"{metric}_change"] = row[f"{metric}_10km"] - row[f"{metric}_500m"]
    results.append(row)


for minimum in (20, 50, 100):
    eligible = [
        event for event in events
        if all(int(by_scale[scale][event]["n"]) >= minimum for scale in by_scale)
    ]
    compare(f"paired_minimum_units_{minimum}", eligible)
compare("equal_weight_for_april_2023_group", events, collapse_april=True)

with (HERE / "matched_scale_sensitivity.csv").open("w", newline="", encoding="utf8") as stream:
    writer = csv.DictWriter(stream, fieldnames=results[0])
    writer.writeheader()
    writer.writerows(results)

for row in results:
    print(row["comparison"], row["events"], row["groups"],
          *(f"{row[x]:.6f}" for x in ("overlap_500m", "overlap_10km",
                                     "spearman_500m", "spearman_10km")))
