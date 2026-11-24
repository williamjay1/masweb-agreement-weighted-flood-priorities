# Missouri USGS field measurements: bounded post hoc search

## Finding

The USGS Short Term Network (STN) official event endpoint returned 334 events, of which the only events with a May 2025 start or end were Pennsylvania (10 to 17 May) and Maryland (6 to 20 May). The `states=MO` high-water mark endpoint returned 287 Missouri records, none in the original bounding rectangle or pertaining to a 2025 event in the returned event names. These are bounded statements about this service response, not evidence that no high-water marks were collected anywhere else. Responses were obtained on 2026-11-15 and their SHA256 is in `USGS_SOURCE_MANIFEST.json`.

The USGS NWIS instantaneous values endpoint returned gage height (parameter 00065, feet) time series for 28 sites in the original bbox [-94.1241, 36.4828, -92.5184, 37.8490]. Query dates were 22 to 31 May 2025 inclusive, with one day of padding because a date-only NWIS request is interpreted in the site's local time. Time stamps were then converted to UTC. Each of the 28 returned sites had at least one value in the analysis window 23 May 00:00 UTC to 28 May 00:00 UTC (exclusive) and at least one reading within one hour of the 30 May 16:48:07 UTC optical L30 acquisition.

A post hoc distance-only selection identified the nearest site to any of the 5,661 original optical eligible common-valid pixel centres, without using water-level outcomes: USGS 07052345, Finley Creek below Riverdale, latitude 36.97488889, longitude -93.3278889. Transforming coordinates to EPSG:5070 gives 535.649920 metres to the nearest pixel centre. The gage is in a river channel, not on a labelled flood polygon or necessarily on eligible agricultural land.

The greatest recorded gage height during the above fixed UTC analysis window was **18.71 ft at 25 May 2025 01:00 UTC**. The nearest reading to the optical L30 time was **3.80 ft at 30 May 16:45 UTC**, a 14.91 ft decrease. Both values carry USGS code A, approved for publication according to https://water.usgs.gov/XML/NWIS/4.8/doc/ReferenceLists/DataAgingList.html. The five-day UTC window contains exactly 480 expected 15-minute records for this site, with no missing slots, duplicates or no-data values; all 480 carry A. The series is gage height referenced to the station's gage datum, not a floodwater depth over fields. It measures a nearby river and does not establish water presence or absence in the optical pixels or provide accuracy, recall or an independently mapped inundation boundary. The decline provides context for temporal mismatch but cannot establish what happened at any specific eligible pixel. Point proximity and temporal stage differences are not validation of the flood maps.

## Reproduction

Get the source NWIS JSON from https://waterservices.usgs.gov/nwis/iv/ with query parameters `format=json`, `bBox=-94.1241,36.4828,-92.5184,37.8490`, `startDT=2025-05-22`, `endDT=2025-05-31`, `parameterCd=00065`, and `siteStatus=all`. Original raw JSON is on the F drive in `external/data/Geocarto_R2_20261115/raw/missouri_usgs_flood_20261115/`; it is immutable. The input optical common point table is `external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv`, originally reconstructed from common-valid eligibility and frozen accepted cells. Packages needed: pandas, scipy, pyproj.

```
python analyze_usgs_gages.py --nwis <padded-usgs-nwis-json> --points <rtc_may26_point_samples.csv> --out <new-output-directory>
```

The script refuses to overwrite an existing output. Its complete 28-site results are `utc_padded/usgs_gages_nearest_joint_domain.csv`, sorted by distance. The retained earlier unpadded input and output are superseded: NWIS date-only endpoints omit the first five UTC hours under a May 23 request in local daylight time; Finley's event peak and comparison nevertheless agree in both queries. Public endpoint documentation: https://api.waterdata.usgs.gov/stnservices/ and https://waterservices.usgs.gov/rest/IV-Service.html. Main station page: https://waterdata.usgs.gov/monitoring-location/USGS-07052345/ .
