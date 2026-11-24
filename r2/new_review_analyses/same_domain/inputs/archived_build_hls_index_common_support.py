"""Build MNDWI and AWEI cell statistics on strict four chain support.

The HLS spectral bands are read from versioned cloud optimized GeoTIFF assets.
Only 30 m pixels inside primary 500 m cells and the existing DSWx strict common
support are evaluated.  The output is a new sufficient statistics database,
not a repackaging of a public water map.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import urllib.parse
import urllib.request
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds


ROOT = Path(__file__).resolve().parents[2]
V4 = Path(__file__).resolve().parents[1]
RESULTS = V4 / "results"
CELLS = RESULTS / "analysis" / "primary" / "primary_500m_cells.parquet"
EVENTS = RESULTS / "primary_event_registry.csv"
ASSETS = RESULTS / "hls_index_asset_manifest.csv"
AUDIT = RESULTS / "hls_index_item_resolution_audit.csv"
STATE_LEDGERS = [
    RESULTS / "expanded_pair_state_ledger.csv",
    RESULTS / "noaa_blind_pair_state_ledger.csv",
]
OUT = RESULTS / "analysis" / "hls_indices"
CELL_DIR = OUT / "cells"
LEDGER = OUT / "hls_index_common_support_ledger.csv"
COMBINED = OUT / "hls_index_500m_cells.parquet"
REPORT = OUT / "hls_index_common_support_report.json"

BLOCK = 1024
CELL_M = 500
BAD_DSWX_QA_BITS = np.uint8(1 | 2 | 4 | 8 | 16 | 32 | 64)
DSWX_NONFILL_BIT = np.uint8(128)
BAD_HLS_FMASK_BITS = np.uint8(1 | 2 | 4 | 8 | 16)
REQUIRED_BANDS = {
    "L30": ["B02", "B03", "B05", "B06", "B07", "Fmask"],
    "S30": ["B02", "B03", "B8A", "B11", "B12", "Fmask"],
}

COUNT_FIELDS = [
    "dswx_strict_common_pixel_count",
    "four_chain_common_pixel_count",
    "dswx_s30_water_pixel_count",
    "dswx_l30_water_pixel_count",
    "mndwi_s30_water_pixel_count",
    "mndwi_l30_water_pixel_count",
    "awei_s30_water_pixel_count",
    "awei_l30_water_pixel_count",
    "dswx_intersection_pixel_count",
    "dswx_union_pixel_count",
    "mndwi_intersection_pixel_count",
    "mndwi_union_pixel_count",
    "awei_intersection_pixel_count",
    "awei_union_pixel_count",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    frame.to_csv(temporary, index=False, encoding="utf-8", float_format="%.12g")
    os.replace(temporary, path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def sas_token(unsigned_href: str, cache: dict[tuple[str, str], str]) -> str:
    parsed = urllib.parse.urlparse(unsigned_href)
    account = parsed.netloc.split(".")[0]
    container = parsed.path.strip("/").split("/")[0]
    key = (account, container)
    if key not in cache:
        endpoint = f"https://planetarycomputer.microsoft.com/api/sas/v1/token/{account}/{container}"
        request = urllib.request.Request(endpoint, headers={"User-Agent": "MASWEB-Geocarto-research/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            cache[key] = json.load(response)["token"]
    return cache[key]


def signed_href(unsigned_href: str, cache: dict[tuple[str, str], str]) -> str:
    separator = "&" if "?" in unsigned_href else "?"
    return unsigned_href + separator + sas_token(unsigned_href, cache)


def encode_keys(x_index: np.ndarray, y_index: np.ndarray) -> np.ndarray:
    return (x_index.astype(np.int64) << np.int64(32)) ^ (y_index.astype(np.int64) & np.int64(0xFFFFFFFF))


def relevant_blocks(dataset: rasterio.DatasetReader, cells: pd.DataFrame) -> list[Window]:
    block_ids: set[tuple[int, int]] = set()
    for row in cells.itertuples(index=False):
        # A one pixel buffer prevents floating point edge loss when a 500 m
        # boundary falls almost exactly on a 30 m raster coordinate.
        left = int(row.x_index) * CELL_M - 30
        right = (int(row.x_index) + 1) * CELL_M + 30
        bottom = int(row.y_index) * CELL_M - 30
        top = (int(row.y_index) + 1) * CELL_M + 30
        candidate = from_bounds(left, bottom, right, top, dataset.transform)
        row_start = max(0, int(math.floor(candidate.row_off)))
        row_stop = min(dataset.height, int(math.ceil(candidate.row_off + candidate.height)))
        col_start = max(0, int(math.floor(candidate.col_off)))
        col_stop = min(dataset.width, int(math.ceil(candidate.col_off + candidate.width)))
        if row_stop <= row_start or col_stop <= col_start:
            continue
        for block_row in range(row_start // BLOCK, (row_stop - 1) // BLOCK + 1):
            for block_col in range(col_start // BLOCK, (col_stop - 1) // BLOCK + 1):
                block_ids.add((block_row, block_col))
    windows = []
    for block_row, block_col in sorted(block_ids):
        row_off = block_row * BLOCK
        col_off = block_col * BLOCK
        windows.append(
            Window(
                col_off,
                row_off,
                min(BLOCK, dataset.width - col_off),
                min(BLOCK, dataset.height - row_off),
            )
        )
    return windows


def filter_assets_to_cell_extent(event_assets: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    left = float(cells["x_index"].min() * CELL_M)
    right = float((cells["x_index"].max() + 1) * CELL_M)
    bottom = float(cells["y_index"].min() * CELL_M)
    top = float((cells["y_index"].max() + 1) * CELL_M)
    target = transform_bounds(5070, 4326, left, bottom, right, top, densify_pts=21)
    keep_items: list[str] = []
    for item_id, group in event_assets.groupby("hls_item_id", sort=True):
        item_path = Path(group["item_json_path"].iloc[0])
        item = json.loads(item_path.read_text(encoding="utf-8"))
        bounds = item.get("bbox")
        if not bounds:
            coordinates = np.asarray(item["geometry"]["coordinates"], dtype=object)
            flat = np.asarray([point for ring in coordinates.tolist() for point in ring], dtype=float)
            bounds = [float(flat[:, 0].min()), float(flat[:, 1].min()), float(flat[:, 0].max()), float(flat[:, 1].max())]
        overlaps = not (
            bounds[2] < target[0] or target[2] < bounds[0]
            or bounds[3] < target[1] or target[3] < bounds[1]
        )
        if overlaps:
            keep_items.append(item_id)
    return event_assets[event_assets["hls_item_id"].isin(keep_items)].copy()


def windows_overlap(a: Window, b: Window) -> bool:
    return not (
        a.col_off + a.width <= b.col_off
        or b.col_off + b.width <= a.col_off
        or a.row_off + a.height <= b.row_off
        or b.row_off + b.height <= a.row_off
    )


def clip_window(window: Window, width: int, height: int) -> Window:
    col0 = max(0, int(math.floor(window.col_off)))
    row0 = max(0, int(math.floor(window.row_off)))
    col1 = min(width, int(math.ceil(window.col_off + window.width)))
    row1 = min(height, int(math.ceil(window.row_off + window.height)))
    return Window(col0, row0, max(0, col1 - col0), max(0, row1 - row0))


def open_items(
    stack: ExitStack,
    event_assets: pd.DataFrame,
    family: str,
    target: rasterio.DatasetReader,
    token_cache: dict[tuple[str, str], str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    family_assets = event_assets[event_assets["sensor_family"].eq(family)]
    for item_id, item_rows in family_assets.groupby("hls_item_id", sort=True):
        bands = dict(zip(item_rows["band"], item_rows["unsigned_href"]))
        if any(band not in bands for band in REQUIRED_BANDS[family]):
            continue
        datasets: dict[str, rasterio.DatasetReader] = {}
        vrts: dict[str, WarpedVRT] = {}
        for band in REQUIRED_BANDS[family]:
            source = stack.enter_context(rasterio.open(signed_href(bands[band], token_cache)))
            datasets[band] = source
            vrt = stack.enter_context(
                WarpedVRT(
                    source,
                    crs=target.crs,
                    transform=target.transform,
                    width=target.width,
                    height=target.height,
                    resampling=Resampling.nearest,
                    src_nodata=source.nodata,
                    nodata=source.nodata,
                )
            )
            vrts[band] = vrt
        reference = datasets[REQUIRED_BANDS[family][0]]
        bounds = transform_bounds(reference.crs, target.crs, *reference.bounds, densify_pts=21)
        destination_window = clip_window(from_bounds(*bounds, target.transform), target.width, target.height)
        items.append(
            {
                "item_id": item_id,
                "family": family,
                "vrts": vrts,
                "window": destination_window,
            }
        )
    return items


def family_block(items: list[dict[str, Any]], family: str, window: Window) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    shape = (int(window.height), int(window.width))
    observed = np.zeros(shape, dtype=bool)
    conflict = np.zeros(shape, dtype=bool)
    mndwi_water = np.zeros(shape, dtype=bool)
    awei_water = np.zeros(shape, dtype=bool)
    for item in items:
        if not windows_overlap(window, item["window"]):
            continue
        arrays = {band: item["vrts"][band].read(1, window=window) for band in REQUIRED_BANDS[family]}
        fmask = arrays["Fmask"].astype(np.uint8, copy=False)
        spectral_bands = [band for band in REQUIRED_BANDS[family] if band != "Fmask"]
        valid = (fmask != 255) & ((fmask & BAD_HLS_FMASK_BITS) == 0)
        for band in spectral_bands:
            valid &= arrays[band] != -9999

        if family == "L30":
            blue, green, nir, swir1, swir2 = (
                arrays["B02"].astype(np.float32), arrays["B03"].astype(np.float32),
                arrays["B05"].astype(np.float32), arrays["B06"].astype(np.float32),
                arrays["B07"].astype(np.float32),
            )
        else:
            blue, green, nir, swir1, swir2 = (
                arrays["B02"].astype(np.float32), arrays["B03"].astype(np.float32),
                arrays["B8A"].astype(np.float32), arrays["B11"].astype(np.float32),
                arrays["B12"].astype(np.float32),
            )
        denominator = green + swir1
        valid_mndwi = valid & np.isfinite(denominator) & (np.abs(denominator) > 1e-6)
        current_mndwi = valid_mndwi & (((green - swir1) / np.where(np.abs(denominator) > 1e-6, denominator, 1.0)) > 0)
        current_awei = valid & ((blue + 2.5 * green - 1.5 * (nir + swir1) - 0.25 * swir2) > 0)
        current_valid = valid_mndwi

        overlap = observed & current_valid
        conflict |= overlap & ((mndwi_water != current_mndwi) | (awei_water != current_awei))
        new = (~observed) & current_valid
        mndwi_water[new] = current_mndwi[new]
        awei_water[new] = current_awei[new]
        observed |= current_valid
    observed &= ~conflict
    mndwi_water &= observed
    awei_water &= observed
    return observed, mndwi_water, awei_water, conflict


def grouped_block_counts(
    qualified_keys: np.ndarray,
    state_s: np.ndarray,
    qa_s: np.ndarray,
    state_l: np.ndarray,
    qa_l: np.ndarray,
    s_valid_hls: np.ndarray,
    s_mndwi: np.ndarray,
    s_awei: np.ndarray,
    l_valid_hls: np.ndarray,
    l_mndwi: np.ndarray,
    l_awei: np.ndarray,
    transform: rasterio.Affine,
    window: Window,
) -> pd.DataFrame:
    rows = np.arange(int(window.row_off), int(window.row_off + window.height), dtype=np.int64)
    cols = np.arange(int(window.col_off), int(window.col_off + window.width), dtype=np.int64)
    x = transform.c + (cols + 0.5) * transform.a
    y = transform.f + (rows + 0.5) * transform.e
    x_index = np.floor(x / CELL_M).astype(np.int64)
    y_index = np.floor(y / CELL_M).astype(np.int64)
    grid_x, grid_y = np.meshgrid(x_index, y_index)
    pixel_keys = encode_keys(grid_x, grid_y)
    in_qualified_cell = np.isin(pixel_keys, qualified_keys)

    s_clean = (state_s <= 1) & ((qa_s & BAD_DSWX_QA_BITS) == 0) & ((qa_s & DSWX_NONFILL_BIT) != 0)
    l_clean = (state_l <= 1) & ((qa_l & BAD_DSWX_QA_BITS) == 0) & ((qa_l & DSWX_NONFILL_BIT) != 0)
    strict = in_qualified_cell & s_clean & l_clean
    rr, cc = np.nonzero(strict)
    if len(rr) == 0:
        return pd.DataFrame(columns=["x_index", "y_index", *COUNT_FIELDS])
    common = strict & s_valid_hls & l_valid_hls
    dswx_s = common & (state_s == 1)
    dswx_l = common & (state_l == 1)
    mndwi_s = common & s_mndwi
    mndwi_l = common & l_mndwi
    awei_s = common & s_awei
    awei_l = common & l_awei

    keys = np.empty(len(rr), dtype=[("x", "<i8"), ("y", "<i8")])
    keys["x"] = grid_x[rr, cc]
    keys["y"] = grid_y[rr, cc]
    unique, inverse = np.unique(keys, return_inverse=True)
    fields = {
        "dswx_strict_common_pixel_count": strict[rr, cc],
        "four_chain_common_pixel_count": common[rr, cc],
        "dswx_s30_water_pixel_count": dswx_s[rr, cc],
        "dswx_l30_water_pixel_count": dswx_l[rr, cc],
        "mndwi_s30_water_pixel_count": mndwi_s[rr, cc],
        "mndwi_l30_water_pixel_count": mndwi_l[rr, cc],
        "awei_s30_water_pixel_count": awei_s[rr, cc],
        "awei_l30_water_pixel_count": awei_l[rr, cc],
        "dswx_intersection_pixel_count": (dswx_s & dswx_l)[rr, cc],
        "dswx_union_pixel_count": (dswx_s | dswx_l)[rr, cc],
        "mndwi_intersection_pixel_count": (mndwi_s & mndwi_l)[rr, cc],
        "mndwi_union_pixel_count": (mndwi_s | mndwi_l)[rr, cc],
        "awei_intersection_pixel_count": (awei_s & awei_l)[rr, cc],
        "awei_union_pixel_count": (awei_s | awei_l)[rr, cc],
    }
    output: dict[str, Any] = {"x_index": unique["x"], "y_index": unique["y"]}
    for name, values in fields.items():
        output[name] = np.bincount(inverse, weights=values.astype(np.int64), minlength=len(unique)).astype(np.int64)
    return pd.DataFrame(output)


def event_cell_output(
    event_id: str,
    base_cells: pd.DataFrame,
    state_rows: pd.DataFrame,
    event_assets: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    by_family = state_rows[state_rows["event_id"].eq(event_id)].set_index("sensor_family")
    s_path = ROOT / by_family.loc["S30", "output_state_relpath"]
    l_path = ROOT / by_family.loc["L30", "output_state_relpath"]
    token_cache: dict[tuple[str, str], str] = {}
    qualified = base_cells[(base_cells["event_id"].eq(event_id)) & base_cells["strict_qualified"]].copy()
    event_assets = filter_assets_to_cell_extent(event_assets, qualified)
    qualified_keys = np.sort(encode_keys(qualified["x_index"].to_numpy(), qualified["y_index"].to_numpy()))
    frames: list[pd.DataFrame] = []
    conflict_totals = {"S30": 0, "L30": 0}

    env_options = {
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
        "GDAL_HTTP_MAX_RETRY": "4",
        "GDAL_HTTP_RETRY_DELAY": "1",
        "VSI_CACHE": "TRUE",
        "VSI_CACHE_SIZE": "50000000",
    }
    with rasterio.Env(**env_options), ExitStack() as stack:
        state_s_ds = stack.enter_context(rasterio.open(s_path))
        state_l_ds = stack.enter_context(rasterio.open(l_path))
        if not (
            state_s_ds.shape == state_l_ds.shape
            and state_s_ds.crs == state_l_ds.crs
            and state_s_ds.transform == state_l_ds.transform
        ):
            raise RuntimeError(f"{event_id}: DSWx state grids differ")
        s_items = open_items(stack, event_assets, "S30", state_s_ds, token_cache)
        l_items = open_items(stack, event_assets, "L30", state_s_ds, token_cache)
        windows = relevant_blocks(state_s_ds, qualified)
        for index, window in enumerate(windows, start=1):
            # The primary MASWEB chain uses the frozen expanded binary state
            # in band 2, matching build_common_support_cells.py exactly.
            state_s = state_s_ds.read(2, window=window)
            qa_s = state_s_ds.read(4, window=window)
            state_l = state_l_ds.read(2, window=window)
            qa_l = state_l_ds.read(4, window=window)
            s_valid, s_mndwi, s_awei, s_conflict = family_block(s_items, "S30", window)
            l_valid, l_mndwi, l_awei, l_conflict = family_block(l_items, "L30", window)
            conflict_totals["S30"] += int(s_conflict.sum())
            conflict_totals["L30"] += int(l_conflict.sum())
            current = grouped_block_counts(
                qualified_keys, state_s, qa_s, state_l, qa_l,
                s_valid, s_mndwi, s_awei, l_valid, l_mndwi, l_awei,
                state_s_ds.transform, window,
            )
            if len(current):
                frames.append(current)
            print(f"  {event_id}: block {index}/{len(windows)}")

    if frames:
        counts = pd.concat(frames, ignore_index=True).groupby(["x_index", "y_index"], as_index=False)[COUNT_FIELDS].sum()
    else:
        counts = pd.DataFrame(columns=["x_index", "y_index", *COUNT_FIELDS])
    keep = [
        "event_id", "pair_id", "x_index", "y_index", "eligible_pixel_count",
        "strict_common_valid_pixel_count", "x_center_m", "y_center_m",
    ]
    result = qualified[keep].merge(counts, on=["x_index", "y_index"], how="left", validate="one_to_one")
    result[COUNT_FIELDS] = result[COUNT_FIELDS].fillna(0).astype(np.int64)
    result["four_chain_common_coverage"] = np.divide(
        result["four_chain_common_pixel_count"], result["eligible_pixel_count"],
        out=np.zeros(len(result), dtype=float), where=result["eligible_pixel_count"].to_numpy() > 0,
    )
    result["four_chain_strict_qualified"] = result["four_chain_common_coverage"].ge(0.95)
    common = result["four_chain_common_pixel_count"].to_numpy(float)
    for product in ["dswx", "mndwi", "awei"]:
        for family in ["s30", "l30"]:
            result[f"{product}_{family}_water_fraction"] = np.divide(
                result[f"{product}_{family}_water_pixel_count"], common,
                out=np.full(len(result), np.nan), where=common > 0,
            )
        result[f"{product}_rank_domain"] = result[f"{product}_union_pixel_count"].gt(0) & result["four_chain_strict_qualified"]

    strict_match = result["dswx_strict_common_pixel_count"].eq(result["strict_common_valid_pixel_count"])
    report = {
        "event_id": event_id,
        "primary_strict_cell_count": int(len(qualified)),
        "processed_block_count": int(len(windows)),
        "resolved_s30_item_count": int(event_assets.loc[event_assets["sensor_family"].eq("S30"), "hls_item_id"].nunique()),
        "resolved_l30_item_count": int(event_assets.loc[event_assets["sensor_family"].eq("L30"), "hls_item_id"].nunique()),
        "four_chain_strict_cell_count": int(result["four_chain_strict_qualified"].sum()),
        "four_chain_common_pixel_count": int(result["four_chain_common_pixel_count"].sum()),
        "dswx_strict_pixel_reconstruction_exact": bool(strict_match.all()),
        "dswx_strict_pixel_mismatch_cell_count": int((~strict_match).sum()),
        "s30_overlap_conflict_pixels": conflict_totals["S30"],
        "l30_overlap_conflict_pixels": conflict_totals["L30"],
    }
    return result, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", action="append", help="Process only this event; may be repeated")
    parser.add_argument("--force", action="store_true", help="Rebuild an existing event output")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    CELL_DIR.mkdir(parents=True, exist_ok=True)
    cells = pd.read_parquet(CELLS)
    events = pd.read_csv(EVENTS)
    event_ids = events["event_id"].tolist()
    if args.event:
        requested = set(args.event)
        unknown = requested - set(event_ids)
        if unknown:
            raise ValueError(f"Unknown events: {sorted(unknown)}")
        event_ids = [event_id for event_id in event_ids if event_id in requested]
    assets = pd.read_csv(ASSETS, dtype=str, keep_default_na=False)
    states = pd.concat([pd.read_csv(path, dtype=str, keep_default_na=False) for path in STATE_LEDGERS], ignore_index=True)
    audit = pd.read_csv(AUDIT, dtype=str, keep_default_na=False)
    audit = audit[audit["resolution_status"].eq("resolved")]

    ledger_rows = []
    for event_id in event_ids:
        destination = CELL_DIR / f"{event_id}_hls_index_500m_cells.parquet"
        if destination.exists() and not args.force:
            frame = pd.read_parquet(destination)
            ledger_rows.append(
                {
                    "event_id": event_id,
                    "status": "reused",
                    "cell_count": len(frame),
                    "four_chain_strict_cell_count": int(frame["four_chain_strict_qualified"].sum()),
                    "output_path": destination.as_posix(),
                    "sha256": sha256(destination),
                }
            )
            continue
        event_assets = assets[assets["event_id"].eq(event_id)].copy()
        print(f"{event_id}: {event_assets['hls_item_id'].nunique()} resolved HLS items")
        result, event_report = event_cell_output(event_id, cells, states, event_assets)
        temporary = destination.with_name(destination.name + ".part")
        result.to_parquet(temporary, index=False, compression="zstd")
        os.replace(temporary, destination)
        ledger_rows.append(
            {
                **event_report,
                "status": "processed",
                "cell_count": len(result),
                "output_path": destination.as_posix(),
                "sha256": sha256(destination),
                "all_requested_s30_items_resolved": bool(
                    audit[(audit["event_id"].eq(event_id)) & audit["sensor_family"].eq("S30")].shape[0]
                    == pd.read_csv(AUDIT).query("event_id == @event_id and sensor_family == 'S30'").shape[0]
                ),
                "all_requested_l30_items_resolved": bool(
                    audit[(audit["event_id"].eq(event_id)) & audit["sensor_family"].eq("L30")].shape[0]
                    == pd.read_csv(AUDIT).query("event_id == @event_id and sensor_family == 'L30'").shape[0]
                ),
            }
        )
        print(json.dumps(event_report, indent=2))

    existing_ledger = pd.read_csv(LEDGER) if LEDGER.exists() else pd.DataFrame()
    current_ledger = pd.DataFrame(ledger_rows)
    if len(existing_ledger):
        existing_ledger = existing_ledger[~existing_ledger["event_id"].isin(current_ledger["event_id"])]
        current_ledger = pd.concat([existing_ledger, current_ledger], ignore_index=True, sort=False)
    current_ledger = current_ledger.sort_values("event_id")
    write_csv(LEDGER, current_ledger)

    primary_files = [CELL_DIR / f"{event_id}_hls_index_500m_cells.parquet" for event_id in events["event_id"]]
    if all(path.exists() for path in primary_files):
        combined = pd.concat([pd.read_parquet(path) for path in primary_files], ignore_index=True)
        temporary = COMBINED.with_name(COMBINED.name + ".part")
        combined.to_parquet(temporary, index=False, compression="zstd")
        os.replace(temporary, COMBINED)
        report = {
            "status": "COMPLETE",
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "event_count": int(combined["event_id"].nunique()),
            "cell_count": int(len(combined)),
            "four_chain_strict_cell_count": int(combined["four_chain_strict_qualified"].sum()),
            "events_with_at_least_three_four_chain_cells": int(
                combined[combined["four_chain_strict_qualified"]].groupby("event_id").size().ge(3).sum()
            ),
            "index_definitions": {
                "MNDWI": "(green minus SWIR1) divided by (green plus SWIR1), water when greater than zero",
                "AWEI": "blue plus 2.5 green minus 1.5 times (NIR plus SWIR1) minus 0.25 SWIR2, water when greater than zero",
            },
            "hls_clean_rule": "Fmask bits 0 through 4 clear and all required reflectance bands nonfill",
            "comparison_support": "existing DSWx strict common support intersected with valid S30 and L30 HLS indices",
            "qualification_rule": "four chain common support covers at least 95 percent of lagged agricultural eligible pixels in a 500 m cell",
            "output_sha256": {COMBINED.name: sha256(COMBINED), LEDGER.name: sha256(LEDGER)},
        }
        write_json(REPORT, report)
        print(json.dumps(report, indent=2))
    else:
        print("Partial run complete; combined output waits for all primary event files.")


if __name__ == "__main__":
    main()
