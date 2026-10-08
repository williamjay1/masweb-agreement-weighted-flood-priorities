[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23238975.svg)](https://doi.org/10.5281/zenodo.23238975)

# Agreement-weighted agricultural flood priorities from discordant optical water maps

Data and code accompanying the manuscript *Agreement Weighted Agricultural Flood Priorities from
Discordant Optical Water Maps* (Geocarto International, manuscript 260353389).

This repository contains the derived analysis inputs, the frozen result tables and the scripts that
reproduce every number and every figure in the manuscript. No new experiment, observation, method
or conclusion is introduced here: the scripts read the released inputs and rewrite the released
outputs in place.

## What the study does

Two optical water products can agree closely on the overall ranking of agricultural units while
selecting different units under a fixed monitoring budget. The manuscript measures that separation
across seven spatial scales, and then evaluates an agreement-weighted capture score against county
insurance indemnity and an independent flood-occurrence endpoint. The independent inferential units
are the five flood events.

## Repository layout

```text
code/                       analysis and figure scripts
  results_audit_support_sensitivity.py   reanalysis at 90%, 95% and 99% common support
  results_audit_numbers.py               rebuilds the manuscript result tables
  make_revision_figures.py               renders Figures 1 to 6 (PDF, SVG, PNG, 1200 dpi TIFF)
data/
  upstream/                 frozen derived inputs read by the scripts
    revision/results/         cell-level counts, product-sensitivity curves, county outcomes
    revision_v2/results/      HLS index cells, threshold-sensitivity metrics, raw RMA utility
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
python results_audit_support_sensitivity.py   # support thresholds, county scores, sign-flip checks
python results_audit_numbers.py               # manuscript result tables
cd ..
python code/make_revision_figures.py          # Figures 1 to 6
```

The scripts resolve all paths relative to the repository root, so a fresh clone runs without editing.
`results_audit_support_sensitivity.py` rewrites `data/derived/support_sensitivity/`,
`results_audit_numbers.py` rewrites the table files in `data/derived/`, and
`make_revision_figures.py` rewrites `figures/`.

### Verified reproduction

Running the three scripts on a fresh copy of this repository reproduces the released outputs:

- 9 of 9 audited CSV and JSON result files are byte-identical after rerun;
- all 6 released TIFF figures are byte-identical, and all 6 PNG previews are pixel-identical;
- PDF and SVG artwork is regenerated with identical content but differs in file bytes because these
  formats embed a creation timestamp;
- all 21 frozen inputs match the SHA-256 values recorded in `INPUT_PROVENANCE.csv`.

## Data provenance and limits

The inputs under `data/upstream/` are derived cell-level and county-level products, not the original
imagery. They were produced from OPERA DSWx-HLS version 1 surface water, Harmonized Landsat and
Sentinel-2 version 2 surface reflectance, USDA Cropland Data Layer, Global Surface Water, NOAA Storm
Events, USDA RMA Cause of Loss records and a Census-derived county layer. The upstream providers are
cited in the manuscript.

The county layer is a frozen semigeneralized Census-derived layer with a publisher label of 2025. It
reports a simplification tolerance of 2 miles, a minimum area of 10 square miles and removal of
components over water. Boundary-simplification sensitivity is not tested here.

The five primary events and the four events with estimable insurance totals are fixed. County utility
intervals are percentile event bootstrap intervals that describe the resampling distribution of four
to five independent units; they are not large-sample confidence guarantees. Two support runs share the
same event identities by construction and do not add independent flood events.

The three-event HLS replication reported in Section 3.4 of the manuscript is a lineage check carried
over from the previously analysed data set. Its per-event cell counts are recorded in
`data/upstream/revision/results/analysis/hls_indices/product_sensitivity/product_event_scale_metrics.csv`,
but the per-event overlap and correlation summaries for that replication are not re-derivable from the
files released here.

## Licence

Code is released under the MIT licence (`LICENSE`). Data tables and figures are released under Creative
Commons Attribution 4.0 (`LICENSE-DATA`).

## Citation

See `CITATION.cff`. The archived release is deposited in Zenodo:

- concept DOI for all versions (use this one): https://doi.org/10.5281/zenodo.23238975

The same identifiers appear in the manuscript data availability statement.
