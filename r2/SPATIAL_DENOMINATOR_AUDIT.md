# Normalized outcome and county perturbation audit

## What the frozen analysis actually computes

Source `geocarto_revision_v2_20260820/inner_data_audit_20260820/scripts/run_robustness_experiments.py`, lines 130 to 165, first aggregates indemnity, planted quantity and liability for matching records **within each event and county**, then calculates for county c in event e:

`Yc = indemnity_c / liability_c` when the county denominator is positive, and `Yc = 0` otherwise.

The capture formula is defined in the R2 manuscript, Section 2.7: `capture = sum_c(w_c Y_c) / sum_c(Y_c)`, with `sum_c w_c = 0.2*n`; lift is `capture / 0.2`. Applying this formula to those county ratios gives a **share of the sum of county-specific indemnity-to-liability ratios**, not `(sum_c w_c * indemnity_c)/(sum_c w_c * liability_c)` and not a liability-weighted aggregate loss ratio. The terminology `aggregate indemnity to liability ratio` in the results and Table 6 is ambiguous and must explicitly distinguish aggregation within a county from aggregation across counties. The source block bootstrap (`run_robustness_experiments.py`, lines 259 to 295) likewise computes the weighted share of the sum of county ratios in each resample.

The same structure applies to county-level indemnity divided by county-level net planted quantity. These outcomes sum ratios with equal county weight, so the resulting concentration measure is not pooled losses per planted unit. The existing 95% support, 20% budget AWC four-event means are reproduced as 1.160247 (net planted) and 1.072830 (liability), confirming that the frozen reported numbers are consistent with this county-ratio interpretation.

## Missing denominator sensitivity

In 5 of 14 Missouri candidate counties both denominators are nonpositive or missing; 3 Wisconsin counties have the same issue, and Wisconsin has no estimable original outcome total. The frozen pipeline uses zero for these undefined county ratios. After excluding these counties and recalculating fractional 20% weights over the remaining candidates, the four-event mean lifts become 0.967131 (net planted) and 0.902767 (liability). The affected Missouri event changes from 1.554613 to 0.782147 (net planted) and from 1.397339 to 0.717088 (liability). This is an exploratory complete-case alternative that changes both the candidate set and the allocation budget. Missingness may be informative, and these values are not automatically unbiased corrections or directly exchangeable with the frozen estimates. The figures above are for 95% support; other thresholds and all event values are in `results/undefined_denominator_complete_case_event.csv` and `results/undefined_denominator_complete_case_summary.csv`.

## County rank perturbation

The program `exploratory_spatial_and_denominator_sensitivity.py` spatially reassigns accepted cells to the original county layer and reproduces all 37 county totals and AWC scores exactly before resampling. It then samples the original number of occupied blocks within each county with replacement, in 2,000 draws for each of two globally anchored block widths (2.5 km and 5 km), preserving paired cell counts in each block. Candidate counties remain fixed and AWC plus fractional 20% selections are recalculated on every draw.

For the South Dakota event, Codington's AWC exceeds Spink's in 48.05% of draws at 2.5 km and 48.95% at 5 km. These are proportions under particular post hoc perturbation schemes, not probabilities about the true order, calibrated uncertainty intervals or independent validation. Blocks are independently sampled within counties, spatial dependence across blocks and counties remains, and one Missouri county has one occupied block and therefore cannot vary under this resampling. Event, observation and classification errors are not represented. Full event and county results and input hashes are in the corresponding `exploratory_block_perturbation_*` files.
