# RMA planted quantity: evidence, reconstruction, and loss-year sensitivity

## Scope and result

The frozen 95% common-support analysis has 37 candidate event–county rows. Reconstructing the archived Cause of Loss (COL) records selected by crop year, event loss month, county, corn/soybean commodity and wet cause codes 31, 44 and 51 yields 194 records across four crop-year/state combinations: 2023 Minnesota and South Dakota, 2024 Iowa, and 2025 Missouri. The selected commodities are corn (0041) and soybeans (0081); the plans are YP (01), RP (02), and RPHPE (03). See `selected_record_commodity_plan_groups.csv` for counts by combination. The 194 source records reproduce the frozen county sums of planted quantity, indemnity and liability to floating-point tolerances of 4.55e-13, 0 and 3.73e-9, respectively; see `county_reconstruction_check.csv`.

All 194 records were matched, using crop year + five-digit county FIPS + commodity code + insurance plan code, to 68 unique reporting groups in official USDA RMA Summary of Business (SOB) reports. Every corresponding SOB group has `CommodityReportingLevelType` = `Acres`; none is unmatched. Row-level and deduplicated mappings are `rma_record_to_official_unit.csv` and `official_quantity_type_by_event_county_plan.csv`. The exact match fields and provider raw report filename are retained there. The queried 2023 Minnesota, 2023 South Dakota, 2024 Iowa, and 2025 Missouri SOB reports respectively contained 428, 276, 569 and 390 county/crop/plan rows, all reported as Acres. They were obtained in November 2026; live reports may change. This is a contemporaneously retrieved provider-metadata crosswalk applied to a previously frozen COL extract, not a claim that the two sources have identical monetary reporting snapshots.

The official COL layout defines field 19, Net Planted Quantity, as adjusted by insured share and notes that quantity units can vary by commodity. The COL file itself has no per-record quantity-type field. The independent official SOB layout separately defines field 18, Quantity Type, and field 19, Net Reported Quantity. Thus the units are supported by group-level official reporting metadata linked to each selected record, not by a unit field printed in each COL source record. Units in these selected groups are acres, not a universal claim about all RMA commodities.

- Official COL layout: https://pubfs-rma.fpac.usda.gov/pub/Web_Data_Files/Summary_of_Business/cause_of_loss/COL_Summary_of_Business_with_Month_All_Years.pdf
- Official SOB state/county/crop layout: https://pubfs-rma.fpac.usda.gov/pub/Web_Data_Files/Summary_of_Business/state_county_crop/SOB_State_County_Crop_with_Coverage_Level_1989_Forward.pdf
- Official example human-readable query: https://public-rma.fpac.usda.gov/apps/SummaryOfBusiness/ReportGenerator/Results?CC=S&CM=0041%2C0081&CY=2023&ORD=CY%2CST%2CCT%2CCM%2CIP&ST=27&IP=01%2C02%2C03
- Official JSON endpoint and exact query parameters are captured inside each `sob_*_by_county_plan.json` file; the generator may be re-run with `fetch_official_county.py`.

The sum of quantities over COL loss records is an insured-share-adjusted **record-aggregated acreage proxy**. Because different cause or stage records may overlap, it is not necessarily distinct physical farmland, total insured cropland, or independently verified flood footprint. The analysis assigns zero to normalized outcomes where denominators are nonpositive; this must remain explicit. The sum of county-specific ratios used in the capture metric must not be described as a pooled dollar-per-acre rate. Matching crop year and loss month alone does not verify that the loss occurred in the event year or date range.

## Loss-year sensitivity

The original method filters crop year and loss month, rather than loss year. One selected record in Spink County, South Dakota (FIPS 46115), has commodity year 2023 and loss year 2022; it is a soybean RP record, wet cause code 31, with 7.4 reported planted acres, $1,935 indemnity, and $1,935 liability. Holding the event candidates, scores, 20% selection budget and tie weights fixed, remove this record from all three county totals, then recompute the three outcome vectors and the 20% capture lift, averaging over the same four positive-indemnity events. This post hoc check tests the effect of that one detected mismatch; it does not establish event-level temporal agreement for the other records.

| Outcome | AWC archived mean lift | AWC excluding mismatched record | S30 archived | S30 excluding record |
|---|---:|---:|---:|---:|
| Indemnity | 2.191778521 | 2.191679758 | 1.447409614 | 1.447397577 |
| County indemnity / planted quantity | 1.160247496 | 1.160286751 | 0.951000686 | 0.951000740 |
| County indemnity / liability | 1.072829863 | 1.072829757 | 0.903060516 | 0.903060517 |

All four score sets and event-level results are in `loss_year_all_outcomes_summary.csv` and `loss_year_all_outcomes_event.csv`. Values are mean capture lifts, not dollar amounts or correlation coefficients.

## Reproducibility

Python 3 with `pandas`, `numpy`, and `requests` is required. Scripts accept portable paths; direct outputs to a suitable working directory. Do not overwrite historical raw records.

```powershell
python fetch_official_county.py --output-dir <new-or-existing-raw-sob-dir>
python rebuild_records.py --col-dir <archived-col-zip-dir> --inputs-dir <archived-analysis-inputs-dir> --output-dir <work-dir>
python match_sob_units.py --sob-dir <raw-sob-dir> --output-dir <work-dir>
python loss_year_normalized_sensitivity.py --inputs-dir <archived-analysis-inputs-dir> --output-dir <work-dir>
```

The fetch script preserves an existing raw JSON and validates total counts; new downloads may represent a later live reporting snapshot. The frozen COL archives used here are in `external/data/remote_sensing_sci_novelty_audit/candidate3_agricultural_hazard_cascade/revision_geocarto_v4/data/raw/rma_cause_of_loss/`. Official SOB JSON sources are in `external/data/Geocarto_R2_20261115/raw/rma_units/`. Analysis input CSVs are in `external/analysis/Geocarto_R2_20261115/continue_20261115/work/supplementary_analysis/inputs/`. All generated outputs and source code are in this report's directory.

SHA-256 of the exact source snapshots:

```text
f02cbcee8e7feebce34ed7c6a286a5a547d1320580e65be6af555a360cc3d5fc  colsom_2023.zip
00193f1328f1476263eb3ed8f3250ab453a5b0ec11f3154c3d499e14782814ad  colsom_2024.zip
ef08c9ad0bca72d4dce7bb528f1e2b0db7deafbc2a1f6a40ecdd8a9ff0bf9b3d  colsom_2025.zip
73d62b61155689992075417e7b20f782c931159e6ef4a89b66f92b432f918eaf  sob_2023_27_corn_soy_by_county_plan.json
e45d710950c6060d59bb6a7ff9eb82c6d7a1f001b70b41e77a5c88e643f4dae2  sob_2023_46_corn_soy_by_county_plan.json
488fa476a3446ce4f150bbfddb8238b2c848360732b7758a2ab8d480ed39897e  sob_2024_19_corn_soy_by_county_plan.json
4fcfb23d209cb1e60939068c1246cc7481c496d9ce691fd3d0a16516a6fdd28b  sob_2025_29_corn_soy_by_county_plan.json
```
