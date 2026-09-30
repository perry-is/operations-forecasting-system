# Operations Forecasting System

A clean-room reconstruction and extension of an Excel-based logistics forecasting and analysis workflow I built and used in operational work.

The original workflow was consulted roughly ten times to examine inventory demand, order and shipping trends, sales progression, recurring patterns, and rough forward-looking behavior. I used it as evidence when operational questions arose or an assumption needed to be checked against available data. There are no formal outcome metrics, so this project makes no claims about forecast accuracy, cost savings, reduced inventory, prevented stockouts, or productivity gains.

## How the system evolved

### Original workflow — actually used

```text
Human → Operational Excel → Forecast / Analysis Excel → Human operational decision
```

The Excel workflow was a practical evidence layer that supported human analysis. It was not enterprise forecasting software or a statistically validated forecasting model.

### Public clean-room rebuild — implemented here

```text
Human → Synthetic operational Excel → Python validation, analysis, and forecasting
      → Generated forecast Excel → Human review and operational decision
```

The public demo reads [the synthetic input workbook](examples/logistics_operations_input.xlsx) in read-only mode and creates [the generated analysis workbook](generated_example/logistics_forecast.xlsx). Python sits between them. Rerunning the demo never writes into or replaces the human-maintained input workbook.

The rebuild adds reproducible validation and normalization, weekly and monthly analysis, customer/category patterns, inventory-demand analysis, explainable projections, scenarios, review states, an append-only forecast history, forecast-versus-actual comparisons, tests, CI, and an audit trail. Every example is fictional.

### Future design extension — not part of the original workflow or runnable demo

```text
Authorized invoice / receipt / order / shipping document
  → controlled extraction
  → proposed facts with evidence and uncertainty
  → conversational human review: approve, correct, or reject
  → approved canonical record
  → logistics and/or bookkeeping workflows
```

The repository includes deterministic proposal/approval interface types to make this boundary testable. It does not implement document extraction, AI, OCR, or a canonical operational database. A proposed intake record cannot pass the canonical admission function until a human decision creates an approved or corrected record.

See [project history](docs/project-history.md) for a fuller account of what was used, what is rebuilt, and what remains a design extension.

## What the public system analyzes

The input workbook has five source sheets:

- `README` supplies the planning snapshot and actuals cutoff.
- `Orders` contains fictional order dates, customers, categories, item IDs, quantities, values, and status.
- `Shipments` contains order-linked shipped quantities and dates.
- `Inventory` contains the snapshot, allocations, minimum and target levels, lead times, criticality, and synthetic unit costs.
- `Operational_Updates` contains dated inbound purchase orders.

The generated workbook produces weekly order/shipping progression, monthly progression, customer/category patterns, inventory demand by month, three monthly forecast periods, preserved forecast snapshots, forecast-versus-actual scores, inventory scenarios, recommendations, a review queue, and an audit view. See [the workbook map](docs/architecture.md).

## Forecasting and decision boundaries

The baseline forecast uses a transparent calendar-day moving average over up to three complete months before the planning date. Missing history is not silently filled with zero. Sparse history, demand spikes, and intermittent patterns receive review flags. The forecast is deterministic and is not an accuracy probability.

Inventory logic keeps distinct values for on-hand stock, available stock after allocations, eligible dated inbound supply, projected stock at lead time, and projected stock over the planning horizon. A confirmed inbound PO can prevent a false reorder. An overdue or undated PO is flagged and withheld from projected availability. Lead-time demand may create an expedite recommendation even when current inventory looks healthy.

Recommendations remain proposals. They include the relevant facts, forecast, inbound evaluations, projected inventory, reason, and review flags. Scenarios vary demand, lead time, or inbound timing without changing source records. The system does not place orders or connect to an ERP.

## Forecast history and forecast versus actual

For each item and target month, the demo assigns a stable forecast ID based on the planning date. It saves the first generated forecast in `generated_example/forecast_history.jsonl`; later runs with the same ID retain that saved forecast. If changed source data would produce a different value for an existing ID, the system keeps the original snapshot, shows the retained value in `Forecast`, and adds a conflict to `Review_Queue`. A new planning date creates new snapshots.

When a full target month is available by the input workbook's actuals cutoff, the comparison includes forecast, actual, absolute error, percentage error when the actual is nonzero, and direction. “Over” means forecast exceeded actual; “under” means forecast was below actual. Percentage error is `absolute error ÷ |actual|` and is blank when actual demand is zero. The workbook includes both history and comparison sheets so prior forecasts remain distinguishable from later actuals.

## Synthetic demo result

With the checked-in synthetic workbook, the demo reads 14 inventory items, 242 fictional order rows, and 242 linked shipment rows. It writes a 14-sheet forecast workbook, maintains 42 monthly forecast snapshots, and scores 42 completed forecast periods against synthetic actuals through September 2026. These figures describe the constructed demo only, not outcomes from the original workflow.

## Run locally

Python 3.11+ is required. The demo uses `openpyxl` to read and write `.xlsx` files. It makes no model/API calls and needs no network once package dependencies are installed.

```sh
python -m pip install -e .
python -m operations_forecasting.demo
python -m unittest discover -s tests -v
```

The console entry point `operations-forecast-demo` runs the same workflow. Optional arguments select the input workbook, output directory, history file, forecast horizon, safety factor, and number of forecast months:

```sh
operations-forecast-demo --input-workbook examples/logistics_operations_input.xlsx --output-dir generated_example --forecast-periods 3
```

The demo overwrites generated reports and the generated analysis workbook. Forecast history is preserved by stable forecast ID. The source workbook is opened read-only and left intact.

## Generated workbook sheets

`Dashboard`, `README`, `Clean_Data`, `Weekly_Analysis`, `Monthly_Analysis`, `Customer_Category_Analysis`, `Inventory_Demand`, `Forecast`, `Forecast_History`, `Forecast_vs_Actual`, `Scenario_Analysis`, `Recommendations`, `Review_Queue`, and `Audit`.

Other generated files include `recommendations.json`, `planning_report.md`, and `audit.jsonl`. The input workbook is source data; generated files are analysis outputs.

## Limitations

- Every workbook row, identifier, date, price, and quantity is synthetic.
- The forecast is a simple operational baseline, not a statistically validated model.
- The order history is simplified and does not model cancellations beyond excluding them, returns, partial allocations, seasonality, promotions, capacity, or supplier constraints.
- Forecast history is a local JSONL file. It is not tamper-proof and has no multi-user locking or database migration support.
- The generated workbook is a report artifact, not an editable operational system of record.
- Human decisions are not captured as approvals in this prototype.
- Future authorized document intake is represented only by type boundaries. No real source documents, extraction, AI provider, OCR, or cross-workflow fact store is included.
- This is a portfolio prototype, not production planning software. A human planner must verify source data and decisions.

## Repository layout

```text
examples/logistics_operations_input.xlsx   synthetic human-maintained source
generated_example/logistics_forecast.xlsx  generated analysis workbook
generated_example/forecast_history.jsonl   preserved monthly forecast snapshots
src/operations_forecasting/                ingestion, analysis, forecast, and outputs
tests/                                     unittest coverage
docs/                                      architecture, history, and decision limits
diagrams/                                  system flow
```

The examples and generated reports are fictional and do not contain employer, customer, supplier, or proprietary operational data.
