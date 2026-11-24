# Missouri NOAA VIIRS same-day comparison: source audit and limitations

## Source and meaning

The fixed study domain comprises the existing 5,661 strict-common valid S30/L30 pixel centres, from 562 accepted 500 m cells. S30 and L30 acquisition times were 2025-05-30 16:58:49 and 16:48:07 UTC. This is a selective, pre-existing evaluation sample, not the complete spatial AOI or an area-weighted estimate.

The following NOAA VIIRS Flood Mapping 1-day GLB019, v2r0 *optical* product and matching TIFF were obtained anonymously, with source paths, SHA256, lengths, source tags and coordinates recorded in `noaa_source_metadata_and_hashes.json`:

- NetCDF: https://noaa-jpss.s3.amazonaws.com/JPSS_Blended_Products/VFM_1day_GLB/NetCDF/2025/05/30/VIIRS-Flood-1day-GLB019_v2r0_blend_s202505301737140_e202505302100370_c202505310317259.nc
- TIFF: https://noaa-jpss.s3.amazonaws.com/JPSS_Blended_Products/VFM_1day_GLB/TIF/2025/05/30/VIIRS-Flood-1day-GLB019_v2r0_blend_s202505301737140_e202505302100370_c202505310317259.tif
- Source archive and training: https://www.ssec.wisc.edu/flood-map-demo/archive-and-training-links/
- Citation: NOAA National Environmental Satellite, Data, and Information Service, Office of Satellite and Product Operations. 2025. *Enterprise/Blended Flood Mapping External Users’ Manual*, version 3.2, April 10, 2025. https://cimss.ssec.wisc.edu/csppgeo/includes/documents/Enterprise_Flood_Mapping_External_Users_Manual.pdf . The document names John Lindeman and update author Jeffrey Augenbaum.

The filenames and `NC_GLOBAL#time_coverage_start/end` give **17:37:14–21:00:37 UTC for the full product domain**, not the individual time for any sampled Missouri grid cell. The daily composite includes observations from Suomi NPP, NOAA-20 and NOAA-21 VIIRS; no valid single-satellite or exact local acquisition time has been established. The product is Level 4, nominal 375 m, gridded at around 0.003372 degrees. It uses optical reflectance, ancillary layers and reference water masks. It is not SAR, not ground observation, and not a 30 m validation reference. NOAA notes cloud and shadow can prevent flood detection (https://vlab.noaa.gov/web/towr-s/viirs-flood-mapping). The public access was verified; the exact conditions of reuse for this individual archive are not separately established here, so verify the provider terms before redistributing the raw data.

## Prespecified sample and method

The plan was recorded in `PREANALYSIS_PLAN.md` before NOAA class extraction. The reproducible script `compare_noaa_viirs.py` transforms the unchanged 30 m centres from EPSG:5070 to longitude/latitude with always_xy, finds nearest source cells, and reports both centres and deduplicated coarse cells. The NetCDF longitude and latitude arrays use degrees east and north; their interpretation as grid-cell centres leads GDAL to represent the upper-left pixel corner half a cell outside the first coordinate. A random spot check through h5py confirmed that GDAL WaterDetection row/column values and the stored NetCDF array agree. This is an explicit coordinate assumption; the GeoTIFF provider-supplied transform differs, so neither representation is independently established here as the authoritative positioning.

Codes documented in manual table 1-10 and the downloaded source: 1 no valid; 15 flood without fraction retrieval; 16 bare land; 17 vegetation; 30 cloud; 50 shadow; 99 normal water; 100–200 water fraction. NOAA's separate algorithm document describes 101–200 as floodwater fractions: https://www.star.nesdis.noaa.gov/jpss/documents/ATBD/ATBD_VIIRS_Flood_Mapping_v1.0.pdf . Values 134, 169, 170 are within the flood fraction class. We did **not** calculate exact percentage values from these codes, because an explicit value-to-percent conversion for this v2 product has not been independently established. Do not treat a VIIRS flood flag as 100% flooded area. QA code 0 is high, 1 moderate, 2 low, and 255 fill. A QA of 0 does not by itself make a cloud pixel an observed land or water pixel: mask on `WaterDetection` as well.

## NetCDF-centre geolocation results, 30 May

Among 742 distinct VIIRS source cells associated with the fixed 5,661 centres: vegetation 17: 730 cells (5,633 centres); cloud 30: 7 (21); normal water 99: 2 (3); flood fraction class: 3 (4). There are 735 non-cloud, non-fill cells (5,640 centres). Vegetation cells include two QA 2 low-quality cells (10 centres); no QA 255 occurs in this sample. The 3 flood fraction cells all have QA 1 moderate quality:

| row | col | NOAA code | QA | sampled 30 m centres | S30 water centres | L30 water centres |
|---:|---:|---:|---:|---:|---:|---:|
| 2137 | 3447 | 134 | 1 | 1 | 0 | 0 |
| 2211 | 3352 | 170 | 1 | 1 | 1 | 1 |
| 2212 | 3352 | 169 | 1 | 2 | 2 | 2 |

The sampled S30 and L30 flags agree at all four centres inside these three NOAA flood cells, with three water and one non-water centre for each. For each sensor, 2/3 NOAA flood cells contain at least one positive sampled 30 m centre. These values do not measure event-scale accuracy or the percentage of a coarse cell that each optical product classified as water. The 30 m sample covers only part of each coarse cell, and native VIIRS cells themselves may not be statistically independent.

## Geolocation sensitivity and other dates

The 30 May TIFF and NetCDF share exact same data values by row and column: 19,784,704 of 19,784,704 equal; however their published transforms place the same array differently. NetCDF first array coordinate is approximately (-105, 45) as pixel centre, whereas GeoTIFF names (-105, 45) as upper-left pixel boundary, and the grid spacing is also slightly different. Of 5,661 centres, 5,345 map to a different row and/or column, and 64 map to a different category. With the TIFF spatial transform, there are 743 cells: 727 vegetation (5,615 centres), 8 cloud (35 centres), 3 normal water (3 centres), and 5 flood fraction cells (8 centres). In these 5 TIFF flood cells, 2 contain at least one S30 water centre and 2 contain at least one L30 water centre; each sensor has 2 positive centres. This sensitivity does not establish which geolocation convention is authoritative. See `tif_20250530_unique_cells.csv` and `netcdf_may30_unique_cells.csv` for exact grids.

For a limited temporal diagnostic under the TIFF transform, the May 29 composite is predominantly cloud: 741 of 743 mapped cells are cloud and two vegetation. On May 26 all 743 mapped cells are cloud. These older dates are not same-date validations, and no claim of flood absence is warranted.

## Reproducibility and interpretation

Run the script using Python 3 with pandas, NumPy, rasterio/GDAL and pyproj; raw sources and frozen inputs remain unchanged. NetCDF QualityFlag and WaterDetection are read at the same NetCDF row/column, not by attaching QA to TIFF coordinates. Output CSVs provide all centres, unique cells, class-by-quality counts and specific flood cell details. The same 30 m pixel-centre matches across imagery do not establish independent fine-resolution ground truth. Only an exploratory, coarse-resolution, cross-optical comparison is supported; unresolved geolocation and local observation times further qualify it. The netCDF container itself emits a GDAL warning about missing geotransform; its individual coordinate-bearing raster subdatasets contain generated transforms.

Independent audit compared GDAL's generated affine indexing with nearest values on the actual NetCDF coordinate arrays. Seven of 5,661 centres received a different column, but their `WaterDetection` and `QualityFlag` codes were unchanged; the reported class and quality counts therefore remain unchanged. At 30 m centre level, the NetCDF and TIFF transforms classify 4 and 8 centres respectively as flood fractions, with intersection 1 and union 11. The differences concern spatial matching and do not imply disagreement in the underlying array values.

An independent nearest-coordinate-axis check found 7 of 5,661 centres at grid boundaries assigned a neighbouring column compared with the affine approximation. All seven remained vegetation with quality code 0, so reported class and quality counts are unchanged. The same independent audit found 4 centres in NetCDF flood cells and 8 in TIFF flood cells, with one common centre. This underscores the unresolved geolocation sensitivity.
