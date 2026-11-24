# Missouri ALOS-2 ScanSAR: bounded search and exploratory backscatter

## Search and data provenance

JAXA's publicly accessible PALSAR-2 ScanSAR Level 2.2 product is a 25 m normalized radar backscatter product, not a mapped flood extent. It is orthorectified and radiometrically terrain corrected: https://www.eorc.jaxa.jp/ALOS/en/dataset/palsar2_l22_e.htm . A public AWS copy provides HH/HV and a separate quality mask; conversion of positive DN to gamma0 decibels is `20*log10(DN)-83`: https://registry.opendata.aws/jaxa-alos-palsar2-scansar/ .

The AWS bucket `https://jaxaalos2.s3.us-west-2.amazonaws.com/` prefix `palsar2/L2.2/2025/` was searched through object-list pagination with orbit prefixes `ALOS2593`, `ALOS2594`, `ALOS2595`. Within the 22–31 May 2025 filename date window, all 479 item JSON records were retrieved without an error; one actual STAC polygon intersects the previously established Missouri bbox [-94.1241,36.4828,-92.5184,37.8490]:

`ALOS2594110700-250524_WBDR2.2GUA`, acquisition timestamp `2025-05-24T06:09:52.016500Z`, sensor PALSAR-2 ScanSAR, L-band, ascending, HH/HV, EPSG:32615. Metadata: https://jaxaalos2.s3.us-west-2.amazonaws.com/palsar2/L2.2/2025/ALOS2594110700-250524_WBDR2.2GUA.json . Its centre-time precedes the May 30 optical acquisitions by 154.6375 hours (L30) and 154.8158 hours (S30). As scene timestamp represents acquisition near its centre, do not claim per-pixel acquisition time to subsecond precision.

The catalogue search is limited to the above public bucket prefix and orbit/date selection; it cannot exclude commercial, different mode, differently indexed or later-added datasets. `search_alos2.py`, complete item records in `search_results.json`, and immutable listing snapshots and item metadata on F permit review. AWS is public and accessible anonymously in this session; whether the user's particular connection can access it has not been independently tested.

## Download, quality and spatial matching

Assets and complete SHA256 values are in `asset_downloads.json`. New immutable raw source files were downloaded to `external/data/Geocarto_R2_20261115/raw/missouri_alos2_aws_followup_20261115/`: HH 473,086,092 bytes, SHA256 `820187d92c856208777be3b9e6dc326a28122e7c1def8cf28566f680692c8c3f`; HV 450,454,012 bytes, SHA256 `6b0026c94759acb93079166691e1be41175d1d1a047bbe487279d5515c658ac0`; mask 817,136 bytes, SHA256 `42682f14d0c16a6d5fe239b499da1ea6fe98a4be3797dd6bf821fd23aa787356`. These files are not bundled; URLs and hashes are included.

Original input: 5,661 strict joint optical valid and eligible 30 m pixel centres, existing file `external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv`. Transform EPSG:5070 to 32615 and sample the containing SAR cell, no interpolation. The prespecified `ANALYSIS_PLAN.md` records the analysis before observing radar values. `sample_alos2.py` produces `alos2_point_samples.csv` and `alos2_summary.json` using rasterio, pandas, NumPy and pyproj. The scene bounding rectangle contains 3,512 optical centres; 176 have QA 0 (no data), 3,336 have QA 1 (valid data); all 3,336 also have positive HH and HV digital numbers, and map to 3,336 distinct SAR grid cells. The STAC polygon contains 3,327 centres, all of which are valid; 9 further valid mask observations lie immediately outside that coarse geometry. The product mask, not the polygon, determines usable source pixels. Distinct raster cells are not assumed statistically independent.

JAXA mask class 0 is no data and 1 is valid; classes 2/3/4/5 denote layover, shadow, ocean and invalid, respectively, not flood classes. See table 3-3 in the [JAXA Level 2.2 product description](https://www.eorc.jaxa.jp/ALOS/en/dataset/pdf/PALSAR2_CARD4L_L2.2_Geotiff_Format_Description_E_20220715.pdf). Independently sampling all 3,512 in-rectangle centres using rasterio.sample produced zero discrepancies with the block sampling in all three bands.

## Predefined four-group descriptive comparison

Groups are defined by May 30 S30 and L30 optical water flags, S0/L0 meaning neither flag is water and S1/L1 both are water. Values are 25th percentile / median / 75th percentile of calibrated gamma0 (dB):

| Optical flags | n | HH dB | HV dB |
|---|---:|---|---|
| S0 L0 | 3,281 | -14.331 / -12.445 / -10.545 | -22.626 / -20.788 / -18.525 |
| S0 L1 | 24 | -12.975 / -12.434 / -10.755 | -23.830 / -22.601 / -20.350 |
| S1 L0 | 10 | -14.329 / -11.676 / -10.647 | -23.640 / -21.297 / -20.376 |
| S1 L1 | 21 | -16.735 / -14.835 / -14.103 | -24.100 / -23.473 / -22.267 |

This retrospective association compares observations about six and a half days apart on a selected domain. Surface moisture, crops, topography, speckle, incidence angle, temporal change and radar and optical support differ; small groups and spatial dependence preclude generalizing these distributions. Do not select any flood threshold from these optical labels, report radar water extent or compute accuracy, claim field truth, or infer which optical product is more accurate. There was no pre-event water classification.

For a limited repeat-track search, orbit numbers `59411-207*n` for n=1..10 and exact frame `0700` returned no JSON in the same AWS 2025 directory. The same frame at orbit 59618 was present on 7 June, well after the optical acquisition. This checks specified prefixes only; it does not establish that no useful pre-event image exists in adjacent frames, other modes or archives. `repeat_track_search.json` and F-drive `priorrepeat_*` XML record results.

Independent polygon-boundary sensitivity: restricting to the 3,327 STAC-polygon centres removes nine valid data-mask observations, all in S0 L0. The restricted S0 L0 count is 3,272, with HH median -12.4616 dB and HV median -20.7983 dB; counts and medians of the other three groups are unchanged. This illustrates the influence of the choice between polygon geometry and the raster valid-data mask; neither is a flood label.
