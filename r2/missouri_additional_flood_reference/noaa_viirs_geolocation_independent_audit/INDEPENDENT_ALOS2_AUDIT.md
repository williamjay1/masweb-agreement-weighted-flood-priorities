# Independent audit of Missouri ALOS-2 comparison

Read-only audit, 15 November 2026. Manuscript and reviewer response were not changed.

## Reproduction

`independent_alos2_check.py` reads the 5,661 original optical sample points and samples the HH and HV source rasters and JAXA quality raster directly using their native geotransforms, selecting the 25 m raster pixel containing each point. All sampled radar indices, HH and HV digital numbers, and mask values agreed point by point with the existing analysis. Results are in `alos2_audit_independent.json`. The COGs are in `external/data/Geocarto_R2_20261115/raw/missouri_alos2_aws_followup_20261115/`; the existing analysis is under `external/analysis/Geocarto_R2_20261115/missouri_flood_reference_followup_20261115/alos2_aws/`.

The source scene timestamp is 2025-05-24 06:09:52.0165 UTC, 154.6375 hours before L30 and 154.8158 hours before S30. Of 5,661 optical centres, 3,512 fall within the radar raster rectangle; 176 of these have mask 0 and 3,336 have mask 1 and positive values in both bands. Each of these 3,336 points occupies a distinct radar cell. Mask interpretation and calibrated backscatter formula were checked against JAXA's [product description](https://www.eorc.jaxa.jp/ALOS/en/dataset/pdf/PALSAR2_CARD4L_L2.2_Geotiff_Format_Description_E_20220715.pdf) and the [AWS product documentation](https://registry.opendata.aws/jaxa-alos-palsar2-scansar/). For positive DN, gamma nought in dB is 20 log10(DN) - 83, equivalent to 10 log10(DN squared) - 83.

| Optical water labels | n | HH median dB | HV median dB |
|---|---:|---:|---:|
| Neither S30 nor L30 | 3281 | -12.444825 | -20.788206 |
| L30 only | 24 | -12.433592 | -22.601387 |
| S30 only | 10 | -11.675986 | -21.296840 |
| Both | 21 | -14.835201 | -23.473000 |

## Catalog geometry sensitivity

Of the 3,336 valid samples, nine lie outside the published STAC geometry even though their source raster mask is 1 and both bands have positive values. All nine are in the neither-water group. Restricting the analysis to the STAC geometry leaves 3,327 samples: neither-water n = 3,272, HH median -12.461590 dB and HV median -20.798312 dB; the other three groups and medians are unchanged. The cause of this catalog boundary discrepancy is not established. The reported sampling is reproducible as a valid-raster-mask definition and should not be described as having been clipped to the STAC footprint.

## Manuscript and response consistency

The checked `integration/work/latex/Manuscript_Clean.tex`, lines 207 and 360, and `integration/work/Response_to_Reviewers_R2.md`, Major Concern 7 and comments 77 and 86, report the correct group order, sample sizes, rounded medians and L30 time gap. Both identify the measurements as descriptive backscatter, not an independent SAR flood classification, simultaneous flood reference, field truth or optical accuracy estimate. These bounds are appropriate. The comparison leaves a representative near-time independent Missouri flood reference unresolved. The descriptive contrast does not establish flooding or statistical significance, especially because the water groups contain 24, 10 and 21 points and are potentially spatially dependent.
