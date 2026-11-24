# Missouri SWOT KaRIn metadata search, 2026-11-15

This is a catalogue and nominal footprint assessment, not an independent flood validation. It uses the 5,661 previously fixed, jointly optically valid eligible agricultural 30 m pixel centres; see `independent_validation_20261115/missouri_followup/MISSOURI_SEARCH_AND_COMPARISON.md`. S30 and L30 were acquired on 2025-05-30 at 16:58:49 and 16:48:07 UTC, respectively.

NASA CMR was queried for `SWOT_L2_HR_PIXC_D`, collection `C3233944986-POCLOUD`, intersecting bbox -94.1241,36.4828,-92.5184,37.8490 during 2025-05-26 to 2025-06-04 UTC. The complete request URL, UTC retrieval time, and hit count are in `query.json`; the unmodified response and 25 unmodified official ISO granule metadata files are saved in `external/data/Geocarto_R2_20261115/raw/missouri_swot_metadata_20261115/`. Each XML contains an exterior geographic bounding polygon in latitude, longitude order. The CMR UMM spatial fields alone provide bounding rectangles; the ISO polygons provide better nominal granule geometry. `granule_footprint_intersections.csv` lists complete granule IDs, start times, time differences relative to S30, counts, and metadata URLs. `swot_nominal_footprints.geojson` records all parsed nominal polygons. Duplicate PID0_01 and PID0_02 granule versions were included in the polygon union, not counted as independent samples.

For each overpass, spatially transform the original EPSG:5070 point centres to EPSG:4326 and count points covered by the union of that pass's ISO polygons. `compare_swot_footprints.py` reproduces the following:

| 2025 UTC nominal pass | Points | S30 water | L30 water | Both optical water |
|---|---:|---:|---:|---:|
| 28 May 03:25:55 to 03:26:25, orbit 033_259 | 2,521 | 22 | 94 | 12 |
| 28 May 14:13:00 to 14:13:30, orbit 033_272 | 1,887 | 29 | 24 | 20 |
| union of both | 4,408 | 51 | 118 | 32 |
| points in both passes | 0 | 0 | 0 | 0 |
| full fixed optical domain | 5,661 | 63 | 148 | 42 |

The passes were about 61.54 and 50.76 hours before S30. The original registered event window was May 23 through May 27; SWOT on May 28 and the optical images on May 30 are both after that interval. The union represents 77.87% of the sample **by nominal granule polygon only**; it does not establish KaRIn observation validity, classification availability, quality, inundation, or spatial accuracy at those points. The displayed water counts derive exclusively from the May 30 optical observations, not from SWOT. The temporal gap is meaningful and the SWOT pixel cloud is a water-mask product, not a directly supplied flood ground truth. The absence of a pixel from a water-focused point cloud must not automatically be treated as an observed dry negative. Even after obtaining the data, quality flags, dry coverage, permanent water, time difference, independence and selection rules must be examined before any agreement calculation.

An unauthenticated HTTPS range request for a relevant file, `SWOT_L2_HR_PIXC_033_272_090L_20250528T141320_20250528T141331_PID0_01.nc`, returned HTTP 401 via NASA Earthdata authorization. Its associated protected browse PNG likewise returned 401, so the preview could not be examined or interpreted. The analogous nominal 089L item returned 401 for its file and browse, its OPeNDAP metadata request returned 401, and an unsigned direct S3 request returned 403. Requests for these assets under the public metadata bucket returned 404. A 401 or 403 does not imply the data do not exist. Authorized Earthdata access or a legitimate public mirror is required to proceed. No SWOT measurement or browse was downloaded or interpreted.

Sources: [NASA SWOT PIXC product](https://data.nasa.gov/dataset/swot-level-2-water-mask-pixel-cloud-data-product-version-d); [NASA CMR search documentation](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html); [CNES/Theia SWOT PIXC description](https://catalogue.theia.data-terra.org/collection/SWOT_L2_HR_PIXC); [SWOT product handbook](https://earthdata.nasa.gov/s3fs-public/2024-06/D-109532_SWOT_UserHandbook_20240502.pdf).
