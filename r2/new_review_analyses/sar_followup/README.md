# SAR follow-up: reproducibility notes

These post hoc comparisons use separately acquired radar observations or an externally generated radar-based flood prediction. None is a field reference or a ground truth accuracy assessment. This folder accompanies the revised manuscript and response, and does not replace the archived original analysis. The three follow-up event domains are the original strict jointly valid 30 m optical pixels within the accepted 500 m cells. They retain the original crop eligibility and optical quality rules. Sensor acquisition time, detection definition, geolocation, resolution and ancillary data differ.

## Inputs and software

The frozen cell file is `../../inputs/primary_500m_cells.parquet`. The original optical states and eligibility rasters are not included here. On the analysis machine their read-only root is:

`external/data/remote_sensing_sci_novelty_audit/candidate3_agricultural_hazard_cascade/revision_geocarto_v4/data/derived/`

It contains `blind_opera_pair_states/<event>/` and `blind_eligibility/<event>/` as referenced by the scripts. The original data and code archive identified in the manuscript does not reproduce the complete raw-imagery pipeline. Raster data are read-only inputs and all output paths in the examples must point to new working directories. A Python environment requires numpy, pandas, pyarrow, rasterio/GDAL, pyproj, scipy and requests. Open the scripts for exact argument details (`python script.py --help`).

## Wisconsin

`wisconsin_followup/` contains the scripts, counts, sensitivity analysis, GFM source rasters and search metadata. `wisconsin_manifest.json` lists selected water and flood URLs and checksums; `SOURCE_SHA256.txt` lists all selected snapshot checksums. Four GFM tiles cover 3,096 eligible optical common pixels in 221 accepted cells, with no mosaic class conflicts. They were acquired about 31 hours after the optical acquisitions. The observed water layer has one positive pixel, S30 has one and L30 has six; neither optical set intersects the radar positive. That sole radar positive has a nonzero advisory flag. Removing nonzero or missing advisory values leaves 2,668 pixels and no radar water positives. The alternative flagged-domain analyses are in the CSV. A nominally perfect dry classification rate would be misleading, and these sparse observations do not establish sensor superiority. The water and flood classes have different definitions.

Example, with placeholders replaced by local paths and run from `wisconsin_followup/`:

```text
python compare_wisconsin_gfm.py --derived-root <derived-root> --gfm-root ./source_snapshots --extra-root ./source_snapshots --cells <primary_500m_cells.parquet> --output <new-output-dir>
python audit_wisconsin_quality.py --derived-root <derived-root> --gfm-root ./source_snapshots --extra-root ./source_snapshots --cells <primary_500m_cells.parquet> --output <new-output-dir>
```

See `WISCONSIN_SAR_AUDIT.md` for coverage, warnings, uncertainty and the bounded catalogue search.

## South Dakota: predicted positive point comparison

`ai4g_followup/southdakota_positive_only.py` reads three published AI for Good flood detection parquet tiles and locates their point centres on the original optical grid. `results_full/` contains the retained per-detection table and manifest; `southdakota_followup/SEARCH_AND_INDEPENDENT_AUDIT.md` reports an independent check. Of 3,229 predictions in accepted cells during the search window, 330 records fall on the original strictly eligible and jointly valid 30 m optical domain. Deduplicating by acquisition date and optical pixel gives 279 unique 30 m pixels, all on 10 April 2023. The 279 categories are: both optical products water 134; only S30 water 2; only L30 water 5; neither water 138. All 330 retained records have `edge_false_positives=0`. The source Sentinel-1 acquisitions are about 4.5 hours before the optical observations.

The parquet lists model-predicted positive locations, not all valid radar observations. It supplies neither a complete negative domain nor field labels. The count is conditional on reported positive locations and is not optical or SAR accuracy, recall, specificity or a full event flood area. We sample point centres without dilation. The dataset guidance recommends an 80 m buffer when generating a flood extent; the present result does not implement that operation and must not be presented as the recommended extent map. The independently generated model detections are predictions, not ground truth. The exploratory Wisconsin positive-only search is also retained but its four detections in accepted cells all fall outside that event's strict optical common-valid 30 m domain.

The three South Dakota parquet inputs are not included because each exceeds 100 MB. Their read-only location when analyzed was `external/data/Geocarto_R2_20261115/raw/ai4g_2023_event_tiles/`. Public dataset: https://huggingface.co/datasets/ai-for-good-lab/ai4g-flood-dataset ; associated publication: https://doi.org/10.1038/s41467-025-60973-1 . Preserve originals on download and verify hashes:

| File | Bytes | SHA-256 | Public relative URL |
|---|---:|---|---|
| N42W099-post-processing.parquet | 398181189 | b594fabde3edf3bc01aa3bae0dd9af14b80750b8af458a56d26f3e24fb9ecba9 | N42/N42W099/N42W099-post-processing.parquet |
| N42W102-post-processing.parquet | 1125442389 | 8464c4cc7aebfb05254f29a784186c7e1b9fd072d5d241441b4928b2c723f396 | N42/N42W102/N42W102-post-processing.parquet |
| N45W099-post-processing.parquet | 488336985 | cfdafc1d7b6ae600392fcbe41c29d246dc320dfbbe27e09c14753554497dbe3a | N45/N45W099/N45W099-post-processing.parquet |

Prefix each relative URL with `https://huggingface.co/datasets/ai-for-good-lab/ai4g-flood-dataset/resolve/main/`. For the unused Wisconsin positive-only search, `N45/N45W093/N45W093-post-processing.parquet` is 61402083 bytes, SHA-256 `28052769f9a8b30e95768f756c1de34e470f86612fa50ece9f4af5d2d6273cda`; it is not packaged. `download_selected_tiles.py` records the original download process and destination. Verify available storage and adjust the destination before use.

Example, with placeholders replaced by actual files:

```text
python southdakota_positive_only.py --tiles <N42W099.parquet> <N42W102.parquet> <N45W099.parquet> --cells <primary_500m_cells.parquet> --derived-root <derived-root> --output <new-output-dir>
```

The alternative backscatter threshold protocol and code in `southdakota_followup/` were drafted as a diagnostic. Their inclusion does not claim that a threshold comparison was completed or that it provides a validated water mask.

## Missouri: coverage diagnostic

`missouri_followup/` contains a 60-day catalogue screen, scripts, counts, a source snapshot and the detailed availability audit. In the original domain of 5,661 eligible optical common pixels in 562 cells, the nearest nonempty searched GFM observation is 26 May 2025, roughly 112.5 hours before the optical pair. It covers 197 pixels in 27 cells; GFM records no observed water among these, while S30 and L30 record 20 and 22 water pixels. These numbers describe only the small shared support. They cannot establish the lack of flooding in the original domain or an accuracy measure. The higher-coverage 21 May image predates the event; the 14 June image is well after the optical pair. Other searched product catalogues and access restrictions are documented in `MISSOURI_SEARCH_AND_COMPARISON.md`.

The selected GFM raster and metadata are in `source_snapshots/`. Its source URL and SHA-256 are in `missouri_may26_manifest.json`. The full 123-scene screening requires all the original GFM files, not only this selected snapshot. They were retained at `external/data/Geocarto_R2_20261115/raw/missouri_gfm_extended_20261115/`; the candidate and coverage CSV files identify the individual scenes. Remote RTC point sampling is a different support operation from GFM raster reprojection and does not establish a flood class. The NASA product metadata snapshot does not represent successful authenticated download or pixel validation.

Example, with placeholders replaced by local paths and run from `missouri_followup/`:

```text
python compare_may26.py --derived-root <derived-root> --cells <primary_500m_cells.parquet> --gfm ./source_snapshots/ENSEMBLE_FLOOD_20250526T002030_VV_NA020M_E084N030T3__ensemble_water_extent.tif --out <new-output-dir>
python screen_all_pixels.py --derived-root <derived-root> --cells <primary_500m_cells.parquet> --gfm-root <full-123-scene-directory> --screen ./gfm_60day_candidate_downloads.csv --output <new-output-file.csv>
```

`screen_rtc_points.py` uses an online catalogue and temporary public access URLs. Inspect its argument help and source before rerunning; no credentials are saved in these outputs.
