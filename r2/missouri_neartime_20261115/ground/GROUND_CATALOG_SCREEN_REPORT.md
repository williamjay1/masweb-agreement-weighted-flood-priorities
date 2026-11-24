# Missouri independent ground and aerial evidence search, 15 November 2026

For the original rectangle [-94.1241, 36.4828, -92.5184, 37.8490] and 2025-05-30 optical observation, no comparable near-time observed flood boundary or pixel labels were obtained in this additional bounded search. This is not evidence that such data do not exist elsewhere. No accuracy statistics or new validation were calculated.

## USGS Short-Term Network high-water marks

USGS describes its Flood Event Viewer as providing observations including high-water marks: https://www.usgs.gov/tools/flood-event-viewer. The current API is https://api.waterdata.usgs.gov/stnservices/ . At 2026-11-14 22:28:08 UTC, GET https://api.waterdata.usgs.gov/stnservices/hwms/filteredhwms/?states=MO returned 287 records. All 287 had non-null latitude and longitude; these are point coordinates, not inundation polygons. Inclusive test of each point against the bounds above gave 0 points inside or on the rectangle. This bounding-box test is not a point-to-sample intersection calculation, and produces no labels for the 5,661 sample centres. Alternate latitude_dd/longitude_dd fields where available did not differ from the used coordinates.

The endpoint returns event_id, event_name and flag_date. The flag date is a high-water-mark flagging date, not the exact flood occurrence time and is not a survey timestamp. This response does not expose a survey date field. For temporal assessment, the 287 event IDs were joined to the separately retrieved /events/ response: every ID matched; the linked event intervals were all historical, with the most recent event named Central US Spring 2019, ending 2019-05-31 UTC. No event interval intersects 2025-05-20 through 2025-06-05; a separate name string check also found no event name containing 2025. This result concerns only records returned by the Missouri state-filtered API at query time. Other USGS or local archives may include observations missing from STN, and high-water marks record peak occurrence, not necessarily the water extent on 2025-05-30 at 16:48 UTC.

## USDA NAIP airborne imagery

USDA describes NAIP as agricultural growing-season aerial imagery: https://naip-usdaonline.hub.arcgis.com/ . POST https://planetarycomputer.microsoft.com/api/stac/v1/search on the naip collection, the stated bbox and 2025-05-20 00:00:00 to 2025-06-05 23:59:59 UTC returned 0 features. The independent full-year 2025 screen for the same bbox returned 26 features, all IDs beginning ar_, dated July 10 to August 6, not the flood observation period. The extreme south of the rectangle crosses the Missouri–Arkansas border, so these Arkansas footprints must not be described as matching Missouri 2025 flood observations. No pagination link remained in either response. These results describe this indexed collection, not all airborne acquisitions or future catalogue updates.

## On-the-ground imagery lead

A KY3 gallery at https://www.ky3.com/gallery/2025/05/26/photos-road-damage-flood-waters-along-finley-river-south-nixa-across-riverdale-bridge/ documents damage near Riverdale Bridge, published 2025-05-26 00:01 UTC. It does not establish precise capture time, visible georeferenced footprints or the condition of any original optical sample on May 30. It is event context, not a contemporaneous agricultural pixel reference.

## Reproducibility and provenance

Script: external/analysis/Geocarto_R2_20261115/missouri_ground_obs_new_20261115/screen_catalogs.py.

Machine-readable query and SHA-256 manifest: external/analysis/Geocarto_R2_20261115/missouri_ground_obs_new_20261115/screen_summary_20261114T222808Z.json.

Retained API responses: external/data/Geocarto_R2_20261115/raw/missouri_ground_obs_new_20261115/20261114T222808Z/.

The script preserves the distinction between response count and observed reference coverage. The event ID/time-interval and non-null coordinate checks were performed independently against the retained JSON.
