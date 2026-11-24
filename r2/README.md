# Supplementary reanalysis for revision R2

This folder contains frozen derived inputs and code for the exploratory analyses added in revision R2, plus the archived 2023 RMA Cause of Loss ZIP needed for the loss-year check. It does not contain raw satellite imagery, the complete event screening procedure, or a raw-to-paper reconstruction. The public R1 archive contains the earlier analyses. This version provides the later inputs and scripts; see [SOURCES.md](SOURCES.md) for provider access, rights and checksums.

The scripts require Python, NumPy, pandas, SciPy and PyArrow. The tested versions were Python 3.12, NumPy 2.5.1, pandas 3.0.5, SciPy 1.18.0 and PyArrow 25.0.0. From this directory, run:

```
python calculate_secondary.py
python exposure_comparators.py
python ties_and_minimum_support.py
python calculate_support_retention.py
python rma_loss_year_sensitivity.py
```

For calculate_support_retention.py and other county-polygon checks, first restore the exact earlier county input as specified in SOURCES.md. The scripts write to `results/`; the input checksums are listed in `INPUT_SHA256.txt`. The archived 500 m cell parquet contains derived counts, not underlying 30 m images. The analyses reproduce 210 original overlap values and 60 existing event/score/support comparisons. Retention is conditional on the extracted eligible cells, not complete county land area. The independent random cutoff tie results are analytical expectations, not independent observational validation or a spatial null model. The support filters and score comparisons are post hoc; RMA exposure rankings are retrospective and outcome associated. The source normalization sets missing or nonpositive denominators to zero, so those values are not defined observed loss rates. See the manuscript for additional limitations.

The `provenance/` tables list the five events' 82 OPERA granule assets and 57 agricultural eligibility source records, with local storage paths removed. These tables document the archived inputs and do not contain the raw source imagery or the entire preprocessing pipeline.

The 2023 RMA ZIP is a copy of the previously archived [USDA Cause of Loss release](https://pubfs-rma.fpac.usda.gov/pub/Web_Data_Files/Summary_of_Business/cause_of_loss/colsom_2023.zip). The loss-year script checks one identified 2022-loss-year record selected under the 2023 commodity year and recalculates the fixed-ranking lift after excluding it. This check does not verify event attribution for other records.

The additional `census_boundary_sensitivity.py` requires pyshp 3.1.6, Shapely 2.1.2 and pyproj 3.7.2. Download the official [2025 TIGER county archive](https://www2.census.gov/geo/tiger/TIGER2025/COUNTY/tl_2025_us_county.zip), SHA-256 `9c6e9d9076abce2670d1de255de3710c35ecca00a7005d88e012dec52d95f763`, and set the environment variable `CENSUS_COUNTY_ZIP` to its local path before running that script. The 84 MB official archive is not included. The check reassigns existing 500 m centres and repools the original candidate counties; it does not rebuild event boundaries, select new events, or recut source imagery.


## Additional review recheck

`event_water_disagreement.py` recomputes common-valid event water totals, Jaccard and binary quantity and allocation disagreement from the frozen cell counts; these comparisons are not independent accuracy assessments.

`exploratory_spatial_and_denominator_sensitivity.py` reproduces original county scores and then performs within-county 2.5 km and 5 km block perturbations (seed 20261115, 2,000 draws per event and size). It requires Shapely 2 and pyproj in addition to the packages above. Blocks are sampled independently between counties, some counties contain a single block, and draws are not confidence intervals or estimates of true ranking probabilities. It also reports a complete-case analysis that removes counties with missing or nonpositive denominators and redefines the 20% candidate budget; it is a joint change of population and budget, not an unbiased correction for missingness. See `SPATIAL_DENOMINATOR_AUDIT.md` and the result manifests.

NASA OPERA DSWx-HLS documentation: [product specification v1.0.0 revision B](https://archive.podaac.earthdata.nasa.gov/podaac-ops-cumulus-docs/web-misc/opera/OPERA_DSWx-HLS_ProductSpec_v1.0.0_D-107395_RevB.pdf); [algorithm theoretical basis document](https://archive.podaac.earthdata.nasa.gov/podaac-ops-cumulus-docs/web-misc/opera/atbd/DSWx-HLS_ATBD_V1_4_DAAC_Distribution.pdf).

`iowa_legacy_cell_overlap.py` compares globally anchored accepted cell keys for the primary Iowa and legacy Nebraska and Iowa acquisitions. Zero shared accepted keys does not establish that full event footprints, weather drivers, or source episodes are independent.


## Additional second-review analyses

See [new_review_analyses/README.md](new_review_analyses/README.md) for the new analyses, input provenance, relative-path execution instructions and limitations. Additional input hashes are in `new_review_analyses/INPUT_SHA256.txt`.

## Repeating the additional comparisons

Run these commands from the r2 directory or the indicated subdirectory. Use a working copy to keep frozen result files intact. The requirements file records package versions for the verified environment; independently distributed datasets are listed in SOURCES.md.

- Run python exact8/check_event_percentiles.py or python rma_annual/annual_exposure_comparison.py to repeat the event resampling and annual exposure checks from bundled inputs.
- Run python -m zipfile -e wbd_provenance/frozen_geometry.zip wbd_provenance and restore the v1.0.5 county input to check the 37 watershed assignments with python wbd_provenance/verify_wbd_assignments.py --wbd-root wbd_provenance/frozen_geometry.
- Run python viirs_formula_20261124/producer_formula_comparison.py --netcdf PATH --geotiff PATH --output-dir OUTPUT for the Missouri VIIRS formula comparison.
- Run python missouri_swot_pixc_20261115/analyze_swot_pixc.py --raw GRANULE_DIRECTORY --out OUTPUT for the Missouri SWOT water point comparison. The exact granule manifest, optical sample and nominal footprint membership are supplied. The script checks source file sizes and MD5 sums before analysis. The strict and exploratory selection policies are described in the analysis documents.

These cross-product checks use observations with different spatial support and, for some products, different dates. They do not yield a field-verified flood extent or a complete contemporaneous reference for Missouri.
