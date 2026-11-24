# Matched-domain exploratory reanalysis

## Reproduce

From this directory, using Python 3 with NumPy, pandas, SciPy and PyArrow:

    python common_primary_four_chain.py
    python verify_provenance.py
    python audit_otsu_support.py
    python otsu_matched_cells_sensitivity.py

Scripts read only inputs and write only results. Input checksums can be verified against archived_common_support_report.json and otsu_support_ledger_stripped.csv. The latter reproduces the Otsu ledger with the old local output path removed. hls_item_resolution_audit_stripped.csv preserves matched granule IDs, acquisition times, item JSON hashes and statuses without local paths. primary_tie_and_support_sensitivity.csv is the previously reproduced primary OPERA metric table. hls_lineage_archived_metrics.csv is the original lineage event metric file and is used only to export existing results for comment 52.

## Origin and what was calculated

hls_index_500m_cells.parquet is copied from the prior project's results/analysis/hls_indices/, with a hash matching the frozen report. It contains count summaries, not source imagery. The archived builder is copied to inputs for inspection. Its function grouped_block_counts forms the pixel-level intersection of the two DSWx valid states and the valid S30 and L30 HLS spectral-index pixels. DSWx, MNDWI and AWEI water counts share that intersected pixel mask. HLS bands and masks had previously been warped with nearest-neighbour resampling onto the stored OPERA projected grid. This is an intersection on that grid, not a claim of perfect native-pixel geolocation.

The HLS index builder selects previously accepted primary 500 m cells, retains cells with joint support at least 95% of eligible pixels, and counts MNDWI > 0 and AWEI shadow > 0. The code uses stored reflectance bands directly as float32 without an explicit scale factor. It requires the absolute MNDWI denominator to exceed 1e-6 in the original stored-band units. The threshold is not stated in physical reflectance units, and the outputs alone do not establish cross-sensor threshold transfer. The analysis evaluates S30 against L30 separately for each algorithm; it is not classification accuracy, pixel validation or an independent flood reference.

common_primary_four_chain.py pools all qualifying common-domain cells, including dry cells, to the 500 m through 30 km grid. It uses k = ceil(0.20 n), coordinate-ordered ties, and an analytical expected overlap under independently randomized cutoff ties, both reported separately. It reports n and flags whether n >= 20. Spearman and Kendall tau-b are missing if either ranking is constant. The separate original replication cohort retains a different domain and is not merged as additional primary events.

Within the five primary events, Iowa and Missouri have all requested source HLS items resolved and all their original accepted 500 m cells qualify; Wisconsin items were resolved but its event output was reused from an old cache, with no full rebuild log, and its index rankings are effectively constant. Minnesota has only 7,551 of 12,643 accepted cells because some L30 assets were not resolved. South Dakota has no L30 HLS source resolved in the frozen mirror and no joint cells. Complete results therefore cover two reliably documented primary events, plus a small degenerate Wisconsin case and a partially covered Minnesota sensitivity. The original ledger marks Wisconsin as reused; granule-item resolution metadata alone does not independently prove how that cache was created.

The DSWx comparison is checked against the original primary 20% table over seven scales for Iowa, Missouri and Wisconsin. All 21 unit counts and coordinate/random-tie overlaps agree; the maximum Spearman difference is 0.0000764 for Iowa, where four original valid pixels do not survive intersection. This validates aggregation/ranking against that derived reference, not reconstruction from raw images or the other index classifications.

## Otsu comparison is not a same-pixel test

Three otsu_cells parquet files were copied from the prior revision's results/threshold_sensitivity/cells/. Their checksums match the old ledger. They contain MNDWI counts using the old Otsu threshold routine, applied to three legacy, not primary, events. The fixed-threshold and Otsu computations used different conflict exclusions, so their accepted 30 m pixel sets can differ. The inputs contain only aggregate pixel counts, not masks: equal counts cannot prove equal pixels. audit_otsu_support.py counts 500 m cells where fixed and Otsu denominators differ, considering cells where both methods qualify; otsu_matched_cells_sensitivity.py compares those same qualifying 500 m cells across scales but retains method-specific denominators. It evaluates a matched-cell, not matched-pixel, sensitivity, and the difference cannot be attributed to threshold alone. It preserves dry cells and reports both tie rules. No new Otsu threshold has been fitted, and no independent ground truth has been added.

At 500 m in Nebraska–Iowa the zero-water-unit fraction for S30/L30 was 99.57% / 98.36% with fixed zero and 89.80% / 91.32% with Otsu. Its observed coordinate overlap was 0.954 / 0.847, whereas the independently randomized cutoff expectation was 0.213 / 0.425, respectively. This describes zero ties and changing detection prevalence; it does not establish which threshold is accurate or that negative Otsu thresholds necessarily failed.

## Data availability for the comparison

- 52: existing three-event, seven-scale lineage results are explicit in hls_lineage_per_event_budget20.csv. These are an export of the earlier analysis, not a new raw-data run.
- 53, 57 and 58: the paired three-algorithm comparison on common valid pixels and all qualifying units is supplied for Iowa and Missouri, with supplementary Minnesota and Wisconsin rows and all counts and limitations. It does not provide five fully resolved primary events, raw masks, independent validation, or a meaningful inferential uncertainty interval from only two complete events.
- 54: Otsu on matched cells and the support discrepancy were diagnosed using previously derived legacy outputs. The actual per-pixel matched-threshold analysis and physical accuracy remain uncompleted.

