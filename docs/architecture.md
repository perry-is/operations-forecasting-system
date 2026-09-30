# Architecture

The runtime implements a two-workbook workflow. A synthetic human-maintained Excel workbook is read as the source record. Python validates and normalizes its contents, performs operational analysis and inventory planning, preserves forecast snapshots, and writes a separate analysis workbook. No step writes back to the input.

| Component | Responsibility |
|---|---|
| `examples/logistics_operations_input.xlsx` | Synthetic source workbook with planning settings, orders, shipments, inventory snapshot, and dated operational updates / purchase orders |
| `models.py` | Immutable item, usage, order, shipment, PO, dataset, and scenario records |
| `ingest.py` | Read-only workbook intake; date and Decimal normalization; validation of IDs, statuses, and references; derive monthly item demand from orders only through the planning date |
| `analysis.py` | Weekly and monthly order/shipping progression, customer/category patterns, item demand history, and lightweight recurring-pattern observations |
| `forecasting.py` | Calendar-day moving average from complete prior months; insufficient-history, spike, and intermittent-use flags |
| `inventory.py` | Dated inbound eligibility and daily inventory projection, including lead-time position and risk dates |
| `purchasing.py` | Explainable order/expedite/monitor/review candidates, suggested quantities, priorities, and review flags |
| `workflow.py` | Baseline plus three what-if scenarios; inputs remain immutable and audit events retain source values and calculation assumptions |
| `forecast_history.py` | Monthly forecasts keyed by planning date, item, and target month; first value persists; later actuals are scored separately |
| `excel.py` | Generated output workbook with dashboard, normalized rows, historical analysis, forecasts, history, comparisons, scenarios, recommendations, queue, and audit |
| `intake.py` | Future-design value types; proposed facts cannot enter the approved-record boundary |
| `reporting.py` | JSON, Markdown, and JSONL files |
| `demo.py` | End-to-end input-workbook read, analysis, history preservation, output-workbook write, reopen, and structural validation |

## Workbook boundaries

### Human-maintained source workbook

- `README`: fixed planning date, actuals cutoff, and source guidance.
- `Orders`: synthetic order lines and customer/category progression.
- `Shipments`: synthetic dated quantities linked to order IDs.
- `Inventory`: current snapshot, allocations, thresholds, lead time, criticality, and optional fictional unit cost.
- `Operational_Updates`: dated PO lines with status; the planning engine excludes overdue, missing-date, unconfirmed, received, or cancelled supply as appropriate.

`ingest.load_data()` opens this workbook through `openpyxl` with `read_only=True, data_only=True`. The package does not save or modify the source workbook.

### Generated analysis workbook

The output workbook separates normalized source rows, historical trends, demand, forecasts, saved snapshots, actual comparisons, planning scenarios, recommendations, review queue, and audit. Its sheets are useful views of implemented calculations; none is an empty placeholder. The `Forecast_History` sheet is populated from the persistent JSONL ledger rather than rebuilt from current forecast candidates.

## History and actuals semantics

The forecast origin date comes from the input workbook. Usage for inventory forecasting is built from non-cancelled order rows up to and including that date. Order/shipping analysis may include rows through `actuals_through`, allowing synthetic later actuals to be compared with forecasts without leaking those later records into the forecast.

Each forecast ID combines origin date, item ID, and target month. On a rerun, an existing ID keeps its original saved forecast quantity and method details. A changed candidate for that ID increments a conflict count, appears in the review queue, and does not replace the saved snapshot or the `Forecast` sheet's retained value. Later forecast origins get new IDs. Completed target months at or before the actuals cutoff receive actual quantity, absolute error, percentage error where actual is nonzero, and over/under/even direction. A zero actual has no percentage error.

The history is a local JSONL file, not a tamper-proof audit service. It has no concurrency controls, signed records, retention controls, or multiuser database semantics.

## Decision and intake boundaries

Facts, projections, recommendations, and human decisions remain separate. Scenario assumptions never mutate source data. Review flags withhold confident purchase quantities for unreliable inputs. Human decisions stay `not_recorded`.

The future intake types in `intake.py` are not called by the workbook demo. `ProposedOperationalRecord` contains extracted candidates, evidence references, and uncertainty. Only `ApprovedOperationalRecord` values bearing `approved` or `corrected` human decisions pass `admit_approved_records()`. No provider or document parser is implemented.

For the original-workflow history and the public-vs-future distinction, see [project history](project-history.md). For the calculation choices, see [forecasting-method](forecasting-method.md) and [decision boundaries](decision-boundaries.md).
