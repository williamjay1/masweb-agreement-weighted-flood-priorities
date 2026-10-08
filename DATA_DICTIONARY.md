# Data dictionary

All paths are relative to the repository root. Every file listed here appears in `CHECKSUMS.sha256`.

## Frozen inputs, `data/upstream/` and `data/ancillary/`

These are read by the scripts and are never modified by them.

### `data/upstream/revision/results/`

| Path | Contents |
|---|---|
| `primary_external_event_county_outcomes.csv` | County-level outcome table for the nine candidate events: NOAA record counts and damage, RMA indemnity, policies indemnified, net determined quantity, loss months, cause codes, FEMA declarations, event dates, regime and selection phase. |
| `analysis/blind_common_support/cells/NB_<event>_500m_cells.parquet` | Per-event 500 m cell table for the five primary events: eligible pixel count, strict common valid pixel count and coverage, S30 and L30 water counts, intersection and union counts, cell centre coordinates. |
| `analysis/hls_indices/cells/<event>_hls_index_500m_cells.parquet` | Per-event 500 m cell table for the three HLS replication events: DSWx, MNDWI and AWEI water counts on shared and product-active domains. |
| `analysis/hls_indices/product_sensitivity/product_budget_curves.csv` | Per-event, per-product overlap coefficient and target replacement fractions across scales and budget fractions. |
| `analysis/hls_indices/product_sensitivity/product_macro_curves.csv` | Macro means of Spearman correlation and Top 10 percent overlap per product, domain and scale. |
| `analysis/hls_indices/product_sensitivity/product_event_scale_metrics.csv` | Per-event, per-product, per-scale unit counts, Spearman, Kendall tau, mean absolute rank gap and water Jaccard. Holds the replication cell counts 7,649, 8,540 and 27,658. |
| `analysis/opera_dswx_multiscale_v1/historical_hls_sar_per_event_metrics.csv` | Per-event scale metrics for the five primary events. |
| `analysis/opera_dswx_multiscale_v1/historical_hls_sar_summary.csv` | Scale summary used for the manuscript Table 3 means and intervals. |
| `analysis/opera_dswx_mechanisms_v1/spatial_mechanisms_summary.csv` | Within-sensor rank persistence, score SD ratio and neighbour correlation per scale. |
| `analysis/operational_validation/operational_unit_scores.parquet` | Unit scores across scales used by the multiscale comparison. |

### `data/upstream/revision_v2/results/`

| Path | Contents |
|---|---|
| `utility_raw_rma/event_utility_metrics.csv` | Per-event capture and lift for each score under the raw RMA indemnity endpoint. |
| `threshold_sensitivity_metrics.csv` | Fixed-threshold and Otsu per-event Spearman and Top 10 percent overlap for the three-event cohort. |
| `threshold_sensitivity/cells/<event>_hls_index_500m_cells.parquet` | Per-event HLS index cell tables used by the threshold comparison. |

### `data/ancillary/`

| Path | Contents |
|---|---|
| `census_counties_2025/counties_2025_semigeneral.geojson` | Frozen semigeneralized Census-derived county polygons with FIPS codes and names. Used for cell-centre county assignment. |

## Released outputs, `data/derived/`

These are rewritten when the scripts are rerun.

| Path | Contents |
|---|---|
| `results_audit_table3_all5.csv` | Table 3 source: per-scale event count, count of events with at least 20 units, Top k overlap mean and 95 percent interval, Spearman mean and 95 percent interval. |
| `results_audit_algorithm_top20.csv` | Table 4 source at the nominal 20 percent budget: per product Spearman mean and overlap mean with contributing event counts. |
| `results_audit_algorithm_10_20_comparison.csv` | The same quantities at both 10 and 20 percent budgets and both minimum-unit rules. |
| `results_audit_otsu_*.csv` | Fixed versus Otsu threshold comparison and its baseline reproduction check. |
| `results_audit_mechanism_correct_labels.csv` | Rank persistence and score SD ratio per scale for S30 and L30. |
| `results_audit_numerical_summary.json` | Key numbers quoted in the manuscript, with the unrounded overlap decrease. |
| `final_sign_flip_verification.json` | All sign assignments enumerated for each threshold and comparison, with one-sided and two-sided tails. |
| `sensor_acquisition_timestamps.csv` | Acquisition dates, times and absolute sensor lags for all pairs, including the separate Michigan sensitivity pair. |
| `figure_evidence_invariance.json` | Evidence that the figure inputs are unchanged across releases. |

### `data/derived/support_sensitivity/`

| Path | Contents |
|---|---|
| `utility_summary.csv` | Capture, lift, interval and exact sign-flip probability for each score at each support threshold. |
| `utility_event_metrics.csv` | The same quantities per event. |
| `paired_lift_differences.csv` | Score-versus-score lift differences with intervals and both tail definitions. |
| `scale_summary.csv` | Per-scale overlap and correlation means with intervals at each support threshold. |
| `scale_event_metrics.csv` | The same quantities per event. |
| `event_support_census.csv` | Eligible, active and assigned cell counts, eligible pixels and common pixels per event and threshold. |
| `county_scores_and_selections.csv` | County scores, selection weights and outcomes per threshold. |
| `south_dakota_county_score_switch.csv` | The two closely ranked South Dakota counties whose order reverses with the support rule. |
| `baseline_*_reproduction.csv` | Comparison of the rerun against the frozen baseline at each threshold. |
| `support_sensitivity_report.json` | Run record: thresholds, fixed events, bootstrap settings, assignment rule and baseline checks. |

### `data/derived/figures_inputs/`

Frozen inputs for the figure renderer, including `figure_style.json`, the per-event mechanism summary, the
algorithm and Table 3 sources, the utility macro summary and `input_manifest.json` with the SHA-256 of each.

## Figures, `figures/`

`Figure1_Study_design` to `Figure6_External_loss_check`, each in PDF, SVG, PNG and native 1200 dpi TIFF.
Figure 1 is the study workflow; Figures 2 to 6 are the scale response, event heterogeneity, within-sensor
diagnostics, algorithm sensitivity and external utility checks.

## Conventions

- Cell counts are accepted 500 m cells, not independent observations. The independent inferential units
  are flood events.
- Intervals are percentile event bootstrap intervals. County utility uses fractional county-equivalent
  budgets with equal sharing at cutoff ties; grid target sets use whole units with k = ceil(q n).
- Exact sign-flip probabilities come from enumerating all sign assignments. The archived helper column
  `exact_sign_flip_p` is one-sided; `paired_lift_differences.csv` also gives the two-sided value.
