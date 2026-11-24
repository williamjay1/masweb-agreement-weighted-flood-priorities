# Missouri Sentinel-1 GRD catalog and footprint audit

## Objective and scope

As a post hoc search for closer radar observations, both Sentinel-1A and Sentinel-1C were eligible in the following independent catalog queries. The bounding rectangle was longitude -94.1241 to -92.5184 and latitude 36.4828 to 37.8490 (EPSG:4326), over 2025-05-20 00:00:00 UTC through 2025-06-10 23:59:59 UTC. Both query results contain six GRD records, all Sentinel-1A; no Sentinel-1C record was returned. This is a statement about these collections, bounds and interval only. Copernicus STAC returned no next link (request limit 100); ASF query had `maxResults=500` and returned six features. Catalog responses were obtained anonymously and saved unmodified in the F drive raw directory given below.

- Copernicus Data Space STAC: `https://stac.dataspace.copernicus.eu/v1/search`, collection `sentinel-1-grd`, bbox and datetime interval above, limit 100. Documentation: https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- Alaska Satellite Facility SearchAPI: `https://api.daac.asf.alaska.edu/services/search/param`, `dataset=SENTINEL-1`, `processingLevel=GRD_HD`, polygon equal to bbox, start and end above, `output=geojson`, `maxResults=500`. Documentation: https://docs.asf.alaska.edu/api/keywords/

The existing `rtc_may26_point_samples.csv` contains the 5,661 pixel centres from the frozen, joint optical valid and eligible domain. Coordinates were transformed from EPSG:5070 to EPSG:4326 and tested against each catalog's reported polygon. Both catalogs yield the same counts. The `geometry_centres` number measures geometric inclusion only and is NOT a valid-pixel count, a radar water detection, or an accuracy estimate. The footprints may include border areas without valid backscatter.

## Scene-by-scene counts

Times below are UTC, differences are against the L30 optical observation at 2025-05-30 16:48:07 UTC. Each GRD record listed is from Sentinel-1A. Paired IDs identify the same acquisition; differing trailing product identifiers and COG processing do not indicate an additional satellite observation.

| Acquisition start UTC | Difference from L30 (hours) | Copernicus GRD ID | ASF GRD ID | Optical common pixel centres in footprint |
|---|---:|---|---|---:|
| 2025-05-21 00:12:10 | -232.599 | S1A_IW_GRDH_1SDV_20250521T001210_20250521T001235_059285_075B7E_1DBB_COG | S1A_IW_GRDH_1SDV_20250521T001210_20250521T001235_059285_075B7E_761A | 0 |
| 2025-05-21 00:12:35 | -232.592 | S1A_IW_GRDH_1SDV_20250521T001235_20250521T001300_059285_075B7E_1A0C_COG | S1A_IW_GRDH_1SDV_20250521T001235_20250521T001300_059285_075B7E_B763 | 5,661 |
| 2025-05-26 00:20:30 | -112.460 | S1A_IW_GRDH_1SDV_20250526T002030_20250526T002055_059358_075E0B_DFDD_COG | S1A_IW_GRDH_1SDV_20250526T002030_20250526T002055_059358_075E0B_1F59 | 471 |
| 2025-05-26 00:20:55 | -112.453 | S1A_IW_GRDH_1SDV_20250526T002055_20250526T002120_059358_075E0B_D6A2_COG | S1A_IW_GRDH_1SDV_20250526T002055_20250526T002120_059358_075E0B_FAED | 0 |
| 2025-06-07 00:20:30 | +175.540 | S1A_IW_GRDH_1SDV_20250607T002030_20250607T002055_059533_076413_7BD2_COG | S1A_IW_GRDH_1SDV_20250607T002030_20250607T002055_059533_076413_6611 | 477 |
| 2025-06-07 00:20:55 | +175.547 | S1A_IW_GRDH_1SDV_20250607T002055_20250607T002120_059533_076413_0C25_COG | S1A_IW_GRDH_1SDV_20250607T002055_20250607T002120_059533_076413_9081 | 0 |

May 21 geometrically covers the whole accepted domain but precedes the May 23 to May 27 registered event, and is about 9.7 days before the optical pair. May 26's geometry includes 471 centres (8.32% of 5,661), but earlier direct source sampling found only 229 valid dual-polarization RTC centres; GFM's separately reprojected categorical common domain contains 197 centres. These have different masks and operations and cannot be interchanged. June 7 is about 7.3 days after the optical pair, outside the event, and geometrically includes only 477 centres (8.43%). No new representative event-level SAR flood verification follows from these searches.

## Evidence and rerun

- `sentinel1_grd_catalog_footprint_screen.csv`: scene-level computations, including S30/L30 water counts within each footprint, which are NOT SAR flood labels.
- `query_sentinel1_grd.py`: preserves original catalog responses, then constructs the geometric screen. It refuses to overwrite raw snapshots. This original collection script uses hard-coded paths; edit its raw, output and point input paths before a fresh network query, and use a new raw output directory so the original snapshots remain unchanged. For an offline rerun without editing these paths, use the parameterized recompute_footprints.py described in README.md.
- Original catalog metadata: `external/data/Geocarto_R2_20261115/raw/missouri_sar_continue_catalog_20261115/`.
- SHA-256: Copernicus snapshot `c5aa7561d7cc7563cff643fb7094bb5737ffc0ce2ed34cacdb1f75b03e065b16`; ASF snapshot `7f7faf91e3c7e91da5d503652e6bfe4f775a943b01c985383b223717b677ca90`.
- Existing point centres: `external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv`.
- Existing actual pixel analysis: `external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/MISSOURI_SEARCH_AND_COMPARISON.md`.

On 2026-11-15, free space was approximately 62 GiB on D, 131 GiB on E and 1.90 TiB on F. Only small raw catalog snapshots were added to F. No raw imagery was overwritten or moved. Geometric results were saved to D.
