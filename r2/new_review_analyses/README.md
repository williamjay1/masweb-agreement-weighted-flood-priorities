# Additional second-review analyses

This directory contains executable post hoc analyses on derived inputs and source manifests for the selected GFM radar products. It does not contain the original optical satellite imagery, a ground-truth flood set, or a full reproduction of the satellite preprocessing. The previous supplementary analyses and input documentation are in the parent directory. The separately acquired GFM comparison is an inter-product, cross-time comparison and not a truth-based classification accuracy assessment.

Python 3 is required with numpy, pandas, scipy, pyarrow, shapely 2 and pyproj. The figure renderer additionally requires matplotlib, SciencePlots, Pillow and an Arial font (font substitution can change the image). The verification environment used numpy 2.5.1, pandas 3.0.5, scipy 1.18.0, pyarrow 25.0.0, shapely 2.1.2 and pyproj 3.7.2. Commands below are relative to this directory; each writes results beside the script. Inputs are under `../inputs` or `same_domain/inputs`. These commands use frozen inputs. Restore the earlier county polygon file from v1.0.5 before the county geometry checks; see ../SOURCES.md.

```
python methods_analysis/recheck_metrics.py
python methods_analysis/aggregate_liability_block.py
python spatial_null/random_placement.py
python spatial_null/spatial_thinning.py
python spatial_null/cutoff_rank_displacement.py
python external_validation/event_overlap_audit.py
python same_domain/common_primary_four_chain.py
python same_domain/verify_provenance.py
python same_domain/audit_otsu_support.py
python same_domain/otsu_matched_cells_sensitivity.py
python spatial_null/draw_figure4.py
```

The execution of these commands was verified from the staged package. All 38 CSV files shared with the analysis archive matched numerically to absolute and relative tolerance 1e-12. The Figure 4 TIFF exactly matched the archived TIFF by SHA-256 in the figure environment. Numerical results can vary slightly across software versions and tied-rank handling; consult the per-analysis manifests and source tables.

`methods_analysis` reconstructs 35 event-by-scale comparisons from derived cell counts and checks the NOAA binary endpoint and HUC8 resampling records. The aggregate liability ratio is separately recalculated after omitting counties with missing or nonpositive liability; its candidate set and budget differ from the original county-ratio capture. It is a post hoc comparison, not the original metric or a confidence interval. The block perturbation uses seed 20261115 and 2,000 resamples per event.

`spatial_null` jointly shuffles paired sensor values among the fixed accepted cell locations, preserving occupancy but breaking spatial structure; seed 20261115, 300 randomizations per event and scale. The randomization is not a spatially autocorrelated null, inferential significance test, or independent validation. Its thinning analysis selects one accepted cell per occupied block with seed 20261116 and 300 draws per event and block size. Thinning changes the population and does not guarantee spatial independence. The cutoff displacement analysis is sensitive to the deterministic resolution of score ties. The figure renderer uses the same summary and a local copy of its plotting style module.

`same_domain` compares DSWx, MNDWI and AWEI on previously derived four-chain common valid pixel counts. Only Iowa and Missouri have full source-item coverage documented for this check; Minnesota has incomplete coverage, Wisconsin reused an earlier cache, and South Dakota has no matched L30 cells. See its analysis README for checksums, assumptions, threshold-unit limitations, and the distinction between common qualifying cells and identical pixel masks. The matched-cell Otsu check uses legacy-event aggregate data; it cannot isolate threshold effects from differences in pixel support.

`external_validation` audits event and county overlap. Its registered legacy bounding-box intersection with the primary candidate-county union is an upper-bound domain comparison, not actual image or flood-footprint intersection. Event omission is a descriptive sensitivity and does not establish weather independence. The county comparison uses accepted cells, which is narrower than the initial candidate sets.

The NOAA endpoint is a county-level binary indicator of at least one flood or flash flood record in the event window. Because records also informed event selection, it is not an independent ground truth. The generic RMA schema permits heterogeneous units. For the five primary events at 95% support, the 194 selected records were matched to 68 official county, crop year, commodity and insurance plan reporting groups; all report acres. The Cause of Loss rows have no unit field, and record-aggregated quantities need not equal deduplicated physical acreage. See `rma_unit_validation/RMA_UNIT_AUDIT.md`.

## Additional checks from the final audit

Run `python methods_analysis/support_repeated_endpoint_enumeration.py`, `python methods_analysis/noaa_all_support_thresholds.py` and `python methods_analysis/eight_event_comparators.py` from any working directory. The first enumerates all 256 ordered four-event bootstrap samples and explains selected repeated endpoints; it does not reconstruct the original random sequence. The NOAA comparison is near-circular. The eight-event comparison shares a weather episode and is not independent validation. `figure2/draw_figure2.py` rebuilds Figure 2 from its supplied derived event scores; the dashed 0.20 line is the nominal budget, while the exact uniform-selection reference is k/n.

`python external_validation/iowa_registry_selection_rule.py` reproduces the archived longitude and latitude rectangle exclusion ratio; it is not a flood or imagery footprint overlap.

## Additional SAR, RMA and figure work

`sar_comparison/SAR_REPRODUCTION_AND_AUDIT.md` explains the two post hoc GFM comparisons, source versions, coverage search, temporal separation, scripts and limitations. The selected GFM source TIFF and catalog snapshots are included in `sar_comparison/gfm_source_snapshots`; original optical state and eligibility rasters are separately required to rerun the full analysis. The 67-scene search and positive and negative coverage results are retained. GFM is a separate SAR acquisition and product, but includes historical reference water and auxiliary data; it is not ground truth.

`rma_unit_validation/RMA_UNIT_AUDIT.md` documents the official quantity-type match and the loss-year sensitivity. Four exact official report snapshots and the selected record-level crosswalk accompany the scripts.

`event_figures/reviewer_55_61_figures.py` reconstructs the event-specific scale figure and score budget comparison from supplied derived CSVs, with a locally bundled style module. The artificial-shift exploratory test is on hold and is not an accuracy validation or part of the reported results. `NEW_VALIDATION_SHA256.txt` records checksums for the additional SAR and RMA files.
