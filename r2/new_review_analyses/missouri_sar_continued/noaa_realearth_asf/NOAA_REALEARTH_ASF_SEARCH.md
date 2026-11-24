# Missouri NOAA RealEarth and ASF bounded search

Post hoc search for the accepted-domain bounding rectangle W -94.1241, S 36.4828, E -92.5184, N 37.8490. Research optical acquisitions were 2025-05-30 UTC. The SSEC flood-product page describes the four C-band experimental products as possibly derived from Sentinel-1, RCM, or Radarsat-2: https://www.ssec.wisc.edu/flood-map-demo/flood-products/. The official API uses exact product time matching and serves product metadata and feature geometries: https://realearth.ssec.wisc.edu/doc/api.php.

## RealEarth product time inventory

Global product times from four `api/products` JSON responses, filtered inclusively to 2025-05-20 through 2025-06-10:

- `C-band-HH-HV-dual-pol`: 0 timestamps: []
- `C-band-HH-HV-dual-pol-m`: 0 timestamps: []
- `C-band-VV-VH-dual-pol`: 1 timestamps: ['20250602.091402']
- `C-band-VV-VH-dual-pol-m`: 1 timestamps: ['20250602.091402']

The sole VV/VH product record is Sentinel-1A, scene `S1A_IW_GRDH_1SDV_20250602T091333_20250602T091402_059465_0761C8_6065`, centred at -27.9411, -57.6116; this lies in South America, outside Missouri. Its shape response states `ACCESSURL: No file(s) found.`. These results are limited to the four queried layers and this date interval; they do not rule out other archives or private products. No applicable SAR raster was downloaded or compared. Metadata may not constitute a comprehensive inventory of all sensor archives.

The NOAA/GMU public archive's own client JavaScript exposes product choices VIIRS 375-m, VIIRS 375-m 5-Day, ABI 1-km, AHI 1-km, Joint VIIRS/ABI and Joint VIIRS/AHI, with no SAR option. This describes that archive's displayed options, not the existence of products elsewhere: https://jpssflood.gmu.edu/ and https://jpssflood.gmu.edu/js/site.js.

## ASF Sentinel-1 GRD catalog

ASF public search returned 2 GRD_HD records intersecting the rectangle from 2025-05-23 00:00:00 to 2025-06-06 23:59:59 UTC:

- `S1A_IW_GRDH_1SDV_20250526T002055_20250526T002120_059358_075E0B_FAED`, 2025-05-26T00:20:55Z
- `S1A_IW_GRDH_1SDV_20250526T002030_20250526T002055_059358_075E0B_1F59`, 2025-05-26T00:20:30Z

These two Sentinel-1A scenes are those already identified on 26 May. A footprint intersection does not establish usable pixels. This search checks ASF Sentinel-1 GRD_HD for this rectangle and time window only; it is not a search of all satellites, processing levels or commercial holdings. Official endpoint: https://api.daac.asf.alaska.edu/services/search/param.

`source_manifest.json` supplies exact request URLs, HTTP status, SHA-256, and read-only source snapshot paths. All snapshots were saved as newly named files on F; this report and manifest are on D. No credentials were used or recorded.
