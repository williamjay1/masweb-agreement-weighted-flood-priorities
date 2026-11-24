# South Dakota SAR follow-up: search and independent audit

## Sources searched

- The earlier Global Flood Monitoring search within seven days yielded six candidate products with zero valid pixels in the selected common area (see the separate existing GFM audit).
- NASA/JPL OPERA DSWx-S1 begins in August 2024 and cannot represent the April 2023 event: https://developers.google.com/earth-engine/datasets/catalog/OPERA_DSWX_L3_V1_S1
- The DLR SWIM_WE STAC query for the South Dakota study bounding box, all of 2023, returned zero items. This is a query result for that endpoint, not proof that no radar water products exist.
- The RAPID archive S3 listing under the 202304 prefix returned no files in that path; do not generalize this single prefix query to other archive locations. https://registry.opendata.aws/rapid-nrt-flood-maps/
- The Microsoft Planetary Computer sentinel-1-rtc STAC search for 9–11 April 2023 and the study area yielded two same-orbit Sentinel-1A VV scenes with scene-centre timestamps 12:43:55 and 12:44:20 UTC on 10 April. Metadata are retained in the new F: raw source directory as an unsigned STAC response. These are radar backscatter measurements, not classified flood reference data.

## Independent audit of AI4G positive-only analysis

The parent team's `ai4g_followup/southdakota_positive_only.py` samples AI4G single-event flood detection coordinates on the original 30 m optical grid and original strict jointly valid domain, deduplicating by date and pixel. Its full results were independently checked: all 330 event-day detections on that common domain have edge_false_positives = 0; they correspond to 279 unique 30 m pixels, with joint S30/L30 classes 134 water/water, 2 water/nonwater, 5 nonwater/water and 138 nonwater/nonwater. Both Sentinel-1 scene files contribute 182 and 148 records respectively. These counts concern reported radar detections only and offer no information about radar nondetections or the full extent, so no accuracy, recall, false-negative count or relative sensor superiority is established.

The AI4G data card recommends unfiltered parquet for single-event studies, and recommends 80 m buffering when creating a flood extent raster. The implemented point-centre sampling uses no such buffer, so do not call it the recommended complete flood extent. Raster alignment, model false positives and false negatives, event evolution during the approximately 4.5 hour temporal gap, and the 20 m detection versus 30 m optical support limit interpretation. https://huggingface.co/datasets/ai-for-good-lab/ai4g-flood-dataset

## Backscatter diagnostic

See analysis_protocol.md for the pre-result threshold specification and its limitations. This optional post hoc single-band exploration is not a validated water or flood product. The original strict optical support has been independently reconstructed as 431,454 pixels across 2,628 accepted cells and reproduces the original S30 and L30 water counts 8,106 and 21,599. RTC acquisition from the cloud and reprojected coverage must finish before any result can be claimed.
