# Independent audit of the Missouri VIIRS geolocation diagnostic

This audit used the original NOAA VIIRS May 30 NetCDF and GeoTIFF plus the JRC Global Surface Water v1.5 1984–2024 occurrence raster. Both NOAA files have 4,448 by 4,448 identical categorical-array values (as established in the prior independent audit), but define different geolocation transforms. The NetCDF coordinate axes have no bounds variable. The mean auxiliary diagnostic cannot establish the producer's intended grid or the true geolocation error.

## Independent area verification

Using seed 2601, 200 normal-water and 100 vegetation cells were sampled from the 401 by 472 diagnostic window. For both geolocation interpretations, `independent_area_spotcheck.py` intersects the rectangles of each NOAA cell and its underlying JRC 30 m cells analytically, weights by exact overlap area, and excludes JRC 255. The 600 independent calculations agreed with the previously computed GDAL averages to an absolute maximum of 2.98e-8. The 2,925 normal-water and 183,649 vegetation class counts were independently reproduced.

The three prior sampled NOAA flood-class cells have coordinate-definition centre separations of 353.053, 353.698 and 353.730 m on the WGS84 ellipsoid. These are separations between the two assumed coordinate transforms, not measured sensor-position errors.

## Missing data and dependence

In the raw JRC source window containing the selected cells, all 36,059,135 raster values differ from 255; the independently resampled validity mask confirms no partial missing coverage in either grid for the 2,925 normal-water or 183,649 vegetation cells. GeoTIFF minus NetCDF average historical frequent water fraction among normal-water cells is +0.015392; with tolerance 1e-7, 1,182 cells increase, 1,057 decrease and 686 are effectively tied. This is not an improvement for each cell.

The normal-water class comprises 129 eight-neighbour spatial components; two components alone contain 1,125 and 876 cells. Treating 2,925 coarse pixels as independent samples would therefore be unjustified. No inferential p-value was computed. The nine-candidate shift diagnostic was retrospectively chosen and assessed using the same auxiliary water data; its higher 49.19% on a half-cell west shift cannot validate that shifted grid.

The NOAA product manual describes auxiliary global water masks assembled from MOD44W, ESA global water data and NLCD 2006. That description does not establish direct use of JRC in the product, but source data, water history and classification inputs can overlap. Moreover, GSW v1.4 helped define the article's agricultural eligibility, while the post hoc diagnostic uses GSW v1.5. The diagnostic is not independent ground truth or a validation of 2025 flood extent.

Sources and machine-readable results are `independent_area_spotcheck.json` and `full_nodata_pair_and_spatial_audit.json`. The latter and `audit_full_pair.py` reproduce the full nodata, pair direction and spatial-component checks. NOAA manual source: https://cimss.ssec.wisc.edu/csppgeo/includes/documents/Enterprise_Flood_Mapping_External_Users_Manual.pdf ; JRC description: https://global-surface-water.appspot.com/download .
