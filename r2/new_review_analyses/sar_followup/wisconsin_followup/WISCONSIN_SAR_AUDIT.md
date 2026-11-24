# Wisconsin GFM follow-up: reproducibility and evidence limits

This is an exploratory comparison with a separately acquired Sentinel-1 product, not ground-truth validation. The recorded NOAA event was 11–30 April 2023. Optical S30 was acquired at 2023-04-14 17:08:49 UTC and L30 at 16:51:36 UTC. Four EODC GFM v3.1.0 archive V02 tiles from adjacent frames at 2023-04-15 23:58:33 and 23:58:58 UTC were mosaicked; the first acquisition was 30 h 49 min 44 s after S30 and 31 h 6 min 57 s after L30. Adjacent frames span 25 seconds. Source URLs and SHA-256 of water/flood rasters are in `wisconsin_manifest.json`; all inputs are individually hashed in `SOURCE_SHA256.txt` and copied into `source_snapshots/`.

A separate public Planetary Computer `sentinel-1-rtc` STAC bbox search for the accepted-domain vicinity, 12–17 April 2023, returned just these two 15 April Sentinel-1A frames and no next page. The query and response are preserved in `source_snapshots/planetarycomputer_sentinel1rtc_20230412_20230417.json`. This establishes the available RTC scenes in that collection and bounded search, not a claim about all sensors. The GFM 14 April tiles were closer in nominal time but had zero valid pixels in the accepted optical common domain.

The code reads eligibility band 6, strict common-valid expanded S30 and L30 states and quality bands, uses precisely the frozen accepted 221 cells, and reproduces every cell's archived common-valid denominator and both optical water counts exactly. Categorical GFM 20 m layers are nearest-neighbour warped to the existing EPSG:5070 30 m target grid; any 0/1 disagreement between overlapping tiles is excluded. For observed water there were zero such conflicts and all 3,096 optical common-valid pixels had a GFM value. S30 mapped one water pixel, L30 six, and GFM observed water one; neither optical water pixel set intersected the GFM water pixel. Rows below are optical nonwater/water and columns GFM nonwater/water:

```
S30 [[3094, 1], [1, 0]]
L30 [[3089, 1], [6, 0]]
```

On its own domain the GFM flood layer was valid for 2,661 optical common pixels and marked zero as flood; S30/L30 mapped one/five water pixels there. Observed water includes a historical reference-water layer and is not identical in definition to flood extent. These extremely low event-water counts do not support stable inference about sensor performance, and overall dry agreement would conceal the one-pixel sampling limit. Pixel observations are spatially dependent and optical and radar images are roughly 31 h apart. A listed 20% grid capture is based on the sum of equal-cell water fractions and coordinate-ordered ties; with one radar-positive cell it is unstable and is not pixel capture or accuracy.

## GFM advisory and exclusion sensitivity

`audit_wisconsin_quality.py` joins advisory and exclusion raster values from the same contributing GFM frames to the observed-water common pixels. If any valid contributing frame has a nonzero advisory value, that target pixel is flagged; 428/3,096 pixels have flag value 2 and the sole radar-observed-water positive lies among these 428. With all flagged pixels and missing flags removed, n=2,668, GFM water=0, S30=1 and L30=6. According to the official 2022 GFM Product Definition Document, flag 2 is a potential rough-water-surface warning (wind may affect the result); it does not prove the local cause of any mismatch: https://extwiki.eodc.eu/gfm_assets/gfm_pdd_v1_4_20220420.pdf . An additional sensitivity excludes any pixel for which a contributing exclusion-mask raster has value 1: 1,002 pixels are removed and n=2,094, GFM water=1, S30=0 and L30=4. Excluding both yields n=1,826, GFM water=0, S30=0 and L30=4. These are changes in evaluated domains, not accuracy improvements or the original main comparison. Full matrices are in `wisconsin_qa_sensitivity.csv`.

Run the following from this directory; Python requires numpy, pandas, pyarrow, rasterio and scipy. The packaged `source_snapshots` folder contains the selected GFM water, flood, advisory, exclusion layers and the STAC response; original optical data and frozen primary-cell parquet must also be supplied.

```powershell
python compare_wisconsin_gfm.py --derived-root <original-derived-root> --gfm-root ./source_snapshots --extra-root ./source_snapshots --cells <primary_500m_cells.parquet> --output <new-output-dir>
python audit_wisconsin_quality.py --derived-root <original-derived-root> --gfm-root ./source_snapshots --extra-root ./source_snapshots --cells <primary_500m_cells.parquet> --output <new-output-dir>
```

`wisconsin_exploratory_cell_metrics.csv` is retained transparently but its priority statistics are not recommended for inferential use. All calculations were executed with the read-only E-drive original masks, source observations on F, and result files on D. No original inputs were overwritten.
