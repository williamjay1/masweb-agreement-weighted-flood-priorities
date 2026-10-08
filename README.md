[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23238975.svg)](https://doi.org/10.5281/zenodo.23238975)

# Agreement-weighted agricultural flood priorities from discordant optical water maps

Data and code for the study of the same title. The repository holds the derived analysis inputs,
the result tables and the scripts that reproduce every number and every figure. No new experiment,
observation, method or conclusion is introduced here: the scripts read the released inputs and
rewrite the released outputs in place.

## What the study does

Two optical water products can agree closely on the overall ranking of agricultural units while
selecting different units under a fixed monitoring budget. The study measures that separation across
seven spatial scales, and then evaluates an agreement-weighted capture score against county insurance
indemnity and an independent flood-occurrence endpoint. The independent inferential units are the
five flood events.

## Repository layout

```text
code/                       analysis and figure scripts
  support_sensitivity.py        90%, 95% and 99% common-support reanalysis, county scores, sign-flip checks
  result_tables.py              rebuilds the result tables quoted in the study
  make_figures.py               renders Figures 1 to 6 (PDF, SVG, PNG, 1200 dpi TIFF)
data/
  upstream/                 frozen derived inputs read by the scripts
    analysis/results/         cell-level counts, product-sensitivity curves, county outcomes
    analysis_v2/results/      HLS index cells, threshold-sensitivity metrics, raw RMA utility
  ancillary/                frozen semigeneralized county geometry (Census-derived, 2025 label)
  derived/                  released result tables, figure inputs and figure style
figures/                    released Figure 1 to Figure 6 artwork
CHECKSUMS.sha256            SHA-256 of every tracked file
DATA_DICTIONARY.md          what each input and output file contains
INPUT_PROVENANCE.csv        origin and SHA-256 of every frozen input
requirements.txt            Python dependencies
```

## Reproducing the results

```bash
pip install -r requirements.txt
cd code
python support_sensitivity.py   # support thresholds, county scores, sign-flip checks
python result_tables.py         # result tables
cd ..
python code/make_figures.py     # Figures 1 to 6
```

The scripts resolve all paths relative to the repository root, so a fresh clone runs without editing.
`support_sensitivity.py` rewrites `data/derived/support_sensitivity/`, `result_tables.py` rewrites the
table files in `data/derived/`, and `make_figures.py` rewrites `figures/`.

### Verified reproduction

Running the three scripts on a fresh copy reproduces the released outputs:

- all released CSV and JSON result files are byte-identical after rerun;
- all 6 released TIFF figures are byte-identical, and all 6 PNG previews are pixel-identical;
- PDF and SVG artwork is regenerated with identical content but differs in file bytes because these
  formats embed a creation timestamp;
- all 21 frozen inputs match the SHA-256 values recorded in `INPUT_PROVENANCE.csv`.

## Data provenance and limits

The inputs under `data/upstream/` are derived cell-level and county-level products, not the original
imagery. They were produced from OPERA DSWx-HLS version 1 surface water, Harmonized Landsat and
Sentinel-2 version 2 surface reflectance, USDA Cropland Data Layer, Global Surface Water, NOAA Storm
Events, USDA RMA Cause of Loss records and a Census-derived county layer.

The county layer is a frozen semigeneralized Census-derived layer with a publisher label of 2025. It
reports a simplification tolerance of 2 miles, a minimum area of 10 square miles and removal of
components over water. Boundary-simplification sensitivity is not tested here.

The five primary events and the four events with estimable insurance totals are fixed. County utility
intervals are percentile event bootstrap intervals that describe the resampling distribution of four
to five independent units; they are not large-sample confidence guarantees. Two support runs share the
same event identities by construction and do not add independent flood events.

The three-event HLS replication is a lineage check carried over from the previously analysed data set.
Its per-event cell counts are recorded in
`data/upstream/analysis/results/analysis/hls_indices/product_sensitivity/product_event_scale_metrics.csv`,
but the per-event overlap and correlation summaries for that replication are not re-derivable from the
files released here.

## Citation

See `CITATION.cff`. The archived release is deposited in Zenodo at
https://doi.org/10.5281/zenodo.23238975, which always resolves to the most recent version.
