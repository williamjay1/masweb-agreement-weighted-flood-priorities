# NASA DSWx-S1 Missouri availability check

This is a bounded post hoc search, not a validation result. The frozen accepted-domain bounding box is west -94.1240251535152, south 36.48288353106287, east -92.51843367167866, north 37.84887566200008. L30 acquisition time is 2025-05-30 16:48:07 UTC; S30 was 2025-05-30 16:58:49 UTC. The established optical common valid support is 5,661 eligible pixels in 562 accepted 500 m cells.

## CMR searches

On 2026-11-15, NASA CMR collection `C2949811996-POCLOUD` was queried for the bounding box. The interval 2025-05-27 16:48:07 to 2025-06-02 16:48:07 UTC returned 0 granules and CMR-Hits 0. The interval 2025-04-30 16:48:07 to 2025-06-29 16:48:07 UTC returned 46 granules, CMR-Hits 46 (one page requested with page_size 200). The nearest five granules are those on May 26 about 00:20 UTC, approximately 112.5 hours before the optical pair. These are granule bounding-box intersections, not proof of valid target-pixel coverage. No scene inside plus/minus three days was identified in this collection and box; this finding does not rule out other radar sensors or collections. Duplicate granules and tile footprints are not independent acquisitions.

Search endpoint: https://cmr.earthdata.nasa.gov/search/granules.json . Complete query arguments and responses are stored read only in `external/data/Geocarto_R2_20261115/raw/missouri_opera_search_20261115/`:

- cmr_plusminus30days.json | 734906 bytes | SHA256 a1f25657bd6843d36f291cb89e2645f9d4938447036a257b2cf6f147731ece92
- cmr_plusminus3days.json | 691 bytes | SHA256 cd8576b0f7381b98a0f5150495051aabb40eaf15cd77033a3d985a375ba48950

## Access checks

The five May 26 product records offer protected B02 binary-water and B01 classification GeoTIFFs. Anonymous HTTPS on a selected B02 asset redirected to `urs.earthdata.nasa.gov` and returned HTTP 401. No Earthdata username, password, token, netrc, or compatible Google Earth Engine configuration was found in standard local environment checks; no credential values were printed, modified or disclosed. Thus no B01 or B02 TIFF was obtained or evaluated. The official catalog also provides an Earth Engine mirror `OPERA/DSWX/L3_V1/S1`, but using it requires an appropriately registered account and project: https://developers.google.com/earth-engine/datasets/catalog/OPERA_DSWX_L3_V1_S1 .

NASA offers browse PNGs of the five May 26 records as public visualizations. All five were downloaded to the new original-material directory `external/data/Geocarto_R2_20261115/raw/missouri_opera_public_browse_20261115/`; URLs, dimensions and hashes are documented in `browse_manifest.json` here. Each PNG is 1024 by 1024 and is a visualization, not the original classification raster. No 30 m pixel statistics were calculated from the previews, and their existence does not solve the coverage and timing limitations. The assets come from the same May 26 radar observation, so they do not constitute another independent acquisition.

No claim is made that data do not exist in another collection, or that those images capture all flooding. OPERA products are water classifications, not ground truth; their processing uses ancillary data and has a different measurement definition from optical maps. The pre-existing GFM 197/5661 overlap is a separate result and cannot be substituted for unobserved DSWx-S1 valid coverage.
