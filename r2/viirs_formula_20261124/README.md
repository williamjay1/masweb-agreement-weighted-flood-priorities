# VIIRS coordinate formula sensitivity

The sensitivity uses zero-based column c and row r with longitude = -105 + c × 0.003372 and latitude = 45 - r × 0.003372. At row 2211, column 3352 these coordinates are (-93.697056, 37.544508). Point coordinates alone do not define the cell footprint or establish whether the stated resolution is exact.

The NetCDF and GeoTIFF WaterDetection arrays were independently reopened and compared index by index: all corresponding values match. The GeoTIFF stores EPSG:4326 and an area transform with spacing 15/4448 degrees; its first cell's outer upper-left is (-105,45). The NetCDF coordinate array and GDAL's derived center grid closely reproduce the stated formula, while the GeoTIFF cell center is a different representation. For the example pixel, the GDAL derived center is (-93.69705522047, 37.54450748582), while the TIFF transform produces center (-93.69435701439, 37.54215377698). The great-circle distance on WGS84 from the formula coordinate to that TIFF cell center is approximately 353.79 m. This is a difference between computationally selected coordinate representations. It is not a measured instrument geolocation error and does not establish the physically correct location. The two numbers are directly comparable as cell centers only under the explicitly stated center assumption.

## Repeated sample sensitivity

The same frozen 5,661 optical sample positions were transformed from EPSG:5070 to EPSG:4326 and sampled from the exact same 4448 by 4448 WaterDetection array. For the formula, a grid support needs to be assumed before points can be assigned to pixels. Two distinct explicit assumptions are therefore tested, each treating the six-decimal resolution as exact. They do not represent provider-confirmed footprints. Flood is defined as code 15 or 101 through 200, as in the earlier analysis.

| Interpretation | Distinct sampled cells | Flood cells | Sample positions assigned flood | Sample positions with differing category versus TIFF | Sample positions with differing binary flood status versus TIFF | Sample positions flood under both |
|---|---:|---:|---:|---:|---:|---:|
| Formula point is assumed cell center | 742 | 3 | 4 | 64 | 10 | 1 |
| Formula point is assumed upper-left cell corner | 721 | 5 | 8 | 22 | 6 | 5 |
| GeoTIFF stored affine transform | 743 | 5 | 8 | 0 | 0 | 8 |

The independent GDAL NetCDF center interpretation has identical category and flood classifications to the exact formula center assumption across all 5,661 positions. Four points are assigned different row or column indices because the fitted GDAL spacing differs slightly from 0.003372; their sampled categories are nevertheless identical. The resulting counts are exploratory sensitivity results and cannot validate the 30 m optical map or establish sensor accuracy. The daily VIIRS product is not independent SAR, and the files do not identify the contributing observation time for each cell.

## Reproducibility

Run `python producer_formula_comparison.py` with rasterio, numpy, pandas, h5py and pyproj, with --netcdf and --geotiff pointing to the original NOAA tiles and --output-dir pointing to a writable directory. The separately distributed NOAA tiles are identified by title in the result JSON. Both matched optical sampling tables are bundled, and the script resolves their paths relative to itself. Outputs are `producer_formula_comparison.json` and the 5,661-row `producer_formula_5661_pointwise.csv`; they include assigned index, class and flood status for each interpretation. The script asserts identical raster values and verifies the original sample coordinates against the archived per-point NetCDF extract. Source files are opened read-only. SHA-256 of the frozen input CSV is recorded in the JSON.
