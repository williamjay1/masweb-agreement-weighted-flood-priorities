# MODIS flood display tiles: screening only

NASA GIBS MODIS_Combined_Flood_1-Day rendered WMTS tiles were sampled on 24, 25, 26, 27 and 30 May 2025 for the 5,661 original eligible common optical pixel centres. The WMTS display tiles and capabilities file were saved without alteration under `external/data/Geocarto_R2_20261115/raw/missouri_flood_gibs_20261115/`; download URLs and SHA-256 checksums are in `tile_manifest.json`. `inspect_modis_display.py` records the coordinate and display-pixel sampling process.

On 25 to 27 May, every sampled centre was rendered grey. On 30 May, every sampled centre was transparent; on 24 May, 4,563 were grey and 1,098 transparent. These are counts of optical centres, not independent MODIS observations; an independent check found 934 unique display grid cells. The official legend associates grey with insufficient observations, while transparency in a rendered tile is not an authoritative substitute for native scientific bands or their quality masks. We did not interpret transparent pixels as dry, calculate accuracy, or infer flood absence. This is a display screening exercise and does not provide a usable field flood reference.

Sources: https://gibs.earthdata.nasa.gov/colormaps/v1.3/MODIS_Flood.xml and https://www.earthdata.nasa.gov/global-flood-product .
