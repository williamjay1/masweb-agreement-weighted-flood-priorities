# Missouri ALOS-2: same repeat-orbit candidate search

## Question and result

Is there an earlier, openly available ALOS-2 ScanSAR L2.2 image on the nominal repeat orbit that intersects the frozen Missouri optical sample, allowing an exploratory pre-event versus 24 May 2025 SAR change analysis? This search found none in the specifically bounded public collection and candidate orbits. Consequently, no new SAR change map, accuracy statistic, or May 30 independent validation was created.

The known image is `ALOS2594110700-250524_WBDR2.2GUA`, acquired on 2025-05-24 at 06:09:52 UTC, approximately 154.8 hours before the 2025-05-30 16:58:49 UTC S30 acquisition. The event scene has valid HH and HV at 3,336/5,661 frozen optical sample centres. It is an earlier radar observation, not a contemporaneous flood reference. The earlier work checked only frame 0700. This follow-up checks every indexed frame within ten preceding candidate repeat-orbit numbers.

## Search protocol and coverage checks

JAXA describes a 14-day repeat cycle of 207 orbits: https://www.eorc.jaxa.jp/ALOS/en/alos-2/obs/pal2_obs_guide_e.htm. We thus screened absolute orbit numbers `59411 - 207*n`, for integers `n=1,...,10`, in JAXA's public AWS ScanSAR L2.2 2025 object namespace. This orbit sequence is a candidate repeat-ground-track definition, not proof that a different acquisition uses the same look direction, beam, incidence angle, polarization, or exact swath. Those would require an additional metadata check if an intersecting scene were found.

We listed the **entire orbit prefix**, with no frame, observation-date or polarization filter, and fetched every `.json` product metadata object under each prefix. The indexed acquisitions that did have metadata range from 2025-01-04 through 2025-05-10. All ten prefixes returned successfully; four contained no objects and six contained between 28 and 42 objects. We fetched and spatially screened all 27 product metadata features with zero retrieval or parsing errors. Their full GeoJSON geometries were each valid polygons. None intersected the WGS84 bbox `[-94.1241, 36.4828, -92.5184, 37.8490]`. This bbox was independently checked against the existing frozen sample file: all 5,661 EPSG:5070 centres, transformed with pyproj to WGS84, fall inside it. Thus the failure to find an intersecting footprint is not due to excluding the fixed sample from the selected rectangle.

The search is limited to this public L2.2 bucket, the ten 2025 repeat-orbit candidates, available catalog metadata at query time, and the bbox. It does not screen other paths, off-track acquisitions, other modes, unpublished or licensed archives, years before 2025, or collections updated after the query. It cannot establish that no radar baseline exists in those resources. An intersecting bbox would still require native quality masks, comparable radar acquisition geometry and event-time analysis before use.

## Reproducibility

Query time: 2026-11-14T23:37:08Z. Machine-readable output with every prefix, item and hash: `external/analysis/Geocarto_R2_20261115/missouri_neartime_viirs_followup_20261115/missouri_new_validation/alos_adjacent_20261114T233708Z.json`.

Read-only source snapshots are in `external/data/Geocarto_R2_20261115/raw/missouri_alos2_adjacent_frames/20261114T233708Z/`; these include all ten S3 XML listings and 27 metadata JSON files. The full script is `external/analysis/Geocarto_R2_20261115/missouri_neartime_viirs_followup_20261115/missouri_new_validation/search_alos_adjacent.py`. Repeat from PowerShell with Python, requests and Shapely installed:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
py -3 'external/analysis/Geocarto_R2_20261115/missouri_neartime_viirs_followup_20261115/missouri_new_validation/search_alos_adjacent.py'
py -3 'external/analysis/Geocarto_R2_20261115/missouri_neartime_viirs_followup_20261115/missouri_new_validation/verify_retained_search.py'
```

The first script creates a new time-stamped F-drive source directory and D-drive result file; catalog contents may change. The second script verifies the original retained snapshot hashes, geometry, intersection, and optical sample containment and writes `verification_retained_search.json`. The existing fixed centres were read from `external/analysis/Geocarto_R2_20261115/independent_validation_20261115/missouri_followup/rtc_may26_point_samples.csv`. Original prior SAR and optical data were not modified. General catalog documentation: https://registry.opendata.aws/jaxa-alos-palsar2-scansar/; official product description: https://www.eorc.jaxa.jp/ALOS/en/dataset/palsar2_l22_e.htm.
