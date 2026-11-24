# Copernicus GFM comparison: source, reproduction, and limits

This is an exploratory inter-product comparison, not a ground-truth accuracy assessment. The original analysis used frozen accepted 500 m cells and strict common 30 m optical samples. We performed no event selection based on agreement values: events were screened for coverage and temporal distance first. Iowa was subsequently added as a post hoc cross-time supplement at the reviewer response team's request, based on candidate coverage and observation dates rather than the resulting agreement.

## Sources

* GFM STAC search: https://stac.eodc.eu/api/v1/search, collection `GFM`; `*_full_bbox_search.json` records a separate query using all accepted grid centers plus 0.01 degrees on each bbox side and ±7 days from the first optical timestamp. The expanded full-bbox query returned the same 67 items as the original sampled-center-bbox query, with no pagination. Results can change as the catalog is updated.
* Data: `external/data/Geocarto_R2_20261115/raw/gfm_event_search_20261115`. JSON catalog responses and unmodified downloaded GFM TIFFs are original inputs. Specific water-product URLs, TIFF SHA-256 hashes and acquisition timestamps are in the event manifests; original TIFF filenames are STAC item IDs followed by `__ensemble_water_extent.tif`. Minnesota also uses the analogous two `__ensemble_flood_extent.tif` TIFFs. Minnesota product metadata states `GFM v3.1.0`, archive V02; Iowa states `GFM v3.1.0`, NRT v3.1.0. Verify independently in the saved STAC JSON. Product processing time is distinct from imagery time.
* Product definitions: European Commission, GFM Product User Manual (2023), pp. 23–25, https://extwiki.eodc.eu/gfm_assets/gfm_pum_v20231005_compressed.pdf. Observed water is the union of observed flood and a historical SAR-based reference water mask. Reference water uses auxiliary Copernicus Global Surface Water Maximum Water Extent, so the comparator cannot be treated as wholly independent from all optical inputs. Flood extent excludes normal reference water and therefore is not physically equivalent to optical mapped water. A 2023 manual describes the product family but should not be represented as a uniquely version-3.1 manual.
* Original optical classified state/QA rasters and eligible cropland: `external/data/remote_sensing_sci_novelty_audit/candidate3_agricultural_hazard_cascade/revision_geocarto_v4/data/derived/`, `blind_opera_pair_states/<event>/` and `blind_eligibility/<event>/`; unmodified existing derived files are read-only.
* Original accepted 500 m cells: `external/analysis/Geocarto_R2_20261115/continue_20261115/work/supplementary_analysis/inputs/primary_500m_cells.parquet`.

## Code and exact rerun

Python packages: numpy, pandas, pyarrow, scipy, rasterio/GDAL. The script paths are parameterized and use exact original masks. Example in PowerShell:

```powershell
python ./compare_gfm_minnesota.py --derived-root "external/data/remote_sensing_sci_novelty_audit/candidate3_agricultural_hazard_cascade/revision_geocarto_v4/data/derived" --gfm-root "external/data/Geocarto_R2_20261115/raw/gfm_event_search_20261115" --cells "external/analysis/Geocarto_R2_20261115/continue_20261115/work/supplementary_analysis/inputs/primary_500m_cells.parquet" --output "external/analysis/Geocarto_R2_20261115/independent_validation_20261115/sar/portable_rerun"
python ./compare_gfm_iowa.py --derived-root "external/data/remote_sensing_sci_novelty_audit/candidate3_agricultural_hazard_cascade/revision_geocarto_v4/data/derived" --gfm-root "external/data/Geocarto_R2_20261115/raw/gfm_event_search_20261115" --cells "external/analysis/Geocarto_R2_20261115/continue_20261115/work/supplementary_analysis/inputs/primary_500m_cells.parquet" --output "external/analysis/Geocarto_R2_20261115/independent_validation_20261115/sar/portable_rerun"
python ./screen_all_pixels.py --derived-root "external/data/remote_sensing_sci_novelty_audit/candidate3_agricultural_hazard_cascade/revision_geocarto_v4/data/derived" --gfm-root "external/data/Geocarto_R2_20261115/raw/gfm_event_search_20261115" --cells "external/analysis/Geocarto_R2_20261115/continue_20261115/work/supplementary_analysis/inputs/primary_500m_cells.parquet" --screen ./gfm_14day_candidate_screen.csv --output ./gfm_all_eligible_pixel_screen.csv
```

For portability, set the four options to equivalent paths on the target computer; the inputs must retain original relative names and content. These commands assume the current directory is this SAR folder. The Minnesota parameterized version was actually rerun; its counts match. The Iowa parameterized script was actually executed to produce the outputs.

## Construction and independent checks

S30 and L30 are jointly restricted to eligibility band 6, valid expanded states band 2, and QA band 4 with bit 128 set and bits 1–64 unset. Only original `strict_qualified` cells are retained. Input dimensions, CRS and transforms must agree. Per-cell 30 m denominators and both optical water counts are checked against the frozen primary table; all 12,643 Minnesota cells and all 28,456 Iowa cells matched. GFM categorical rasters are nearest-neighbor reprojected from 20 m to the exact optical EPSG:5070 30 m grid; values 0/1 are nonwater/water and 255 is nodata in these data. Mosaic conflicts (both classes in overlapping inputs) are excluded, not resolved by selecting the preferred value; none occurred in either comparison.

Independent sampling of 20 Minnesota cells found three cells differed by one GFM positive pixel each from direct source-grid coordinate sampling; remaining cells matched. Differences can arise near transformed raster boundaries or from warp approximations; quote results to sensible precision, not as exact ground truth. Spatial pixels are dependent and no independent-sample confidence interval is asserted.

## Coverage and results

The full per-item 30 m coverage table is `gfm_all_eligible_pixel_screen.csv`; a zero count refers to jointly valid eligible pixels, not merely a tile bounding box. Minnesota 14 catalog items, two valid at 2023-04-14 00:14:43 UTC: 2,742,390 / 2,742,390 pixels when mosaicked. Wisconsin 19 items, one useful 2023-04-15 23:58:33 tile has 2,996 / 3,096 pixels and just one water pixel; another three adjacent tiles add coverage and are at 23:58:33 or 23:58:58. South Dakota 6 items, zero valid pixels. Iowa 12 items, four useful May 21 tiles span 00:05:32–00:06:22; mosaicked 5,696,766 / 5,980,411 pixels. Missouri 16 items, best May 26 tile covers 197 / 5,661 and contains zero water pixels; May 31 has zero eligible valid pixels. Positive counts are scene-specific and must not be naively summed in the presence of overlap.

Minnesota S30 = 2023-04-12 17:19:01 UTC, L30 = 17:04:45 UTC, GFM = April 14 00:14:43 UTC: GFM is later by 30h55m42s and 31h09m58s respectively. On the 2,742,390-pixel shared domain, S30 / L30 / GFM water counts are 168,134 / 215,400 / 30,840. Binary counts use rows optical nonwater/water and columns GFM nonwater/water:

```
S30 [[2,573,141, 1,115], [138,409, 29,725]]
L30 [[2,526,224,   766], [185,326, 30,074]]
```

S30 and L30 contain 96.38% and 97.52% of GFM water pixels, respectively; 17.68% and 13.96% of S30 and L30 water pixels, respectively, match GFM water. Positive intersection-over-union is 17.56% and 13.91%. All are symmetric cross-product comparison counts or explicitly conditioned fractions, not estimates of truth-based sensitivity or precision.

Iowa optical S30 = 2024-05-25 16:58:49 UTC and L30 = 16:58:28 UTC, almost 113 hours *after* the May 21 GFM acquisitions. The radar date falls within the registered May 20–22 event, but the optical dates do not; these maps are explicitly cross-time, not contemporaneous. Of 28,456 original cells, 26,409 contain at least one common pixel; 2,047 have none. Common counts are S30/L30/GFM = 44,000 / 55,745 / 9,955, respectively. Matrices:

```
S30 [[5,643,190, 9,576], [43,621, 379]]
L30 [[5,631,473, 9,548], [55,338, 407]]
```

Overlap is very low: 3.81% and 4.09% of GFM-positive pixels and 0.86% and 0.73% of S30/L30-positive pixels, respectively; positive intersection-over-union 0.71% and 0.62%. Water dynamics, differing product definitions, observational errors, and grid effects are possible explanations; these outputs cannot establish their relative importance. Do not hide this result or claim validation of event-time flood extent.

`*_exploratory_cell_metrics.csv` provides post hoc grid-fraction correlations and top-20% capture; the latter sums radar water fraction with equal cell weights, and tie order is fixed by coordinates. It is not radar-positive pixel capture and does not validate agricultural priority rankings or prove a product superior. Overall agreement is dominated by dry pixels and is not a sufficient evaluation. GFM advisory flags were not separately masked in this comparison.

`compare_gfm_missouri.py` and its `confusion_30m.csv` / `common_eligible_30m_pixels.csv` outputs document the zero-overlap May 31 test only; the script stops when asked to calculate cell summaries for an empty common domain. Use the full pixel screening table for Missouri coverage; do not treat that stopped diagnostic as a completed positive comparison.
