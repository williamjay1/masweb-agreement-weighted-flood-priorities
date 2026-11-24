# Missouri SAR follow-up: event-specific search and reproducibility

This folder documents a post hoc availability search for the originally accepted Missouri optical common-valid domain. It does not provide a new flood classification or independent event-level accuracy validation.

Two independent Sentinel-1 GRD catalog snapshots are preserved. Both yield six granules in the specified bbox and 20 May to 10 June 2025 interval. The May 26 footprint contains 471/5,661 original optical pixel centres; geometric inclusion does not guarantee a valid SAR sample. The existing GFM classification was valid at only 197 optical common-valid pixels and contains zero observed-water pixels. The May 21 footprint contains all 5,661 centres and the main GFM tile is valid at 5,633, but its acquisition precedes the May 23 to 27 recorded event and the optical pair by approximately 233 hours. The selected results follow from archived point locations and catalog footprints, not raster water truth.

To independently rerun all 12 geometric rows offline, install pandas, pyproj and shapely, then run from this directory:

```sh
python recompute_footprints.py --catalog-dir . --points ../sar_followup/missouri_followup/rtc_may26_point_samples.csv --output ./footprint_check_new.csv
```

The script refuses to overwrite an existing output. Its recomputed table has been checked against every row of `sentinel1_grd_catalog_footprint_screen.csv`. It reads frozen optical-domain point centres; columns concerning optical water are not radar classifications. Original catalog query code and constraints are in `query_sentinel1_grd.py` and `GRD_CATALOG_AND_FOOTPRINT_AUDIT.md`.

The `nasa_opera/` and `noaa_realearth_asf/` subfolders document separately bounded searches, downloaded response snapshots, and access limitations. Anonymous access to the identified NASA DSWx-S1 B02 classification returned HTTP 401; browse images are visual previews, not the 30 m classification data. No NASA pixel comparison is claimed. The NOAA/RealEarth queries concern only the specified experimental layers and dates; they do not prove absence from all other archives.

The previous SAR follow-up package contains the GFM analysis, manifests, processed per-pixel values and data source descriptions in `../sar_followup/missouri_followup/`. Catalog snapshots and imagery are copied from read-only source files; original raw observations remain at their documented F-drive locations. Existing source raster and optical input dependencies, when required for full processing beyond the offline footprint check, are documented in the earlier follow-up README.
