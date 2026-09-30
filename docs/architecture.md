# Architecture

The current pipeline is a set of deterministic Python functions over frozen dataclasses. It has no external integrations and never executes purchases.

| Module | Responsibility |
|---|---|
| `models.py` | Immutable item, usage, purchase-order, dataset, and scenario records |
| `ingest.py` | Parse CSV fields to dates, Decimal quantities, and normalized records; reject duplicate/unknown keys and malformed values |
| `forecasting.py` | Select complete calendar months, calculate the daily average, and flag weak history |
| `inventory.py` | Explain receipt eligibility and project daily stock using dated supply |
| `purchasing.py` | Check snapshot quality and produce candidate actions, quantities, deadlines, and review flags |
| `workflow.py` | Apply baseline and scenario assumptions without editing input records; assemble audit records |
| `reporting.py` | Summarize recommendations and write JSON, Markdown, and JSONL |
| `demo.py` | Load the fictional fixtures at a fixed as-of date and run all four scenarios |

## Data contracts

CSV item quantities are distinct from purchase-order quantities. A PO reference identifies one synthetic line; multi-line production POs would need an explicit line ID in a future schema. Duplicate item IDs, usage months for an item, and PO references stop ingestion. Unknown item references, unrecognized PO statuses, non-finite numbers, and malformed dates also stop ingestion rather than becoming forecasts.

Recognizable but weak inputs such as a negative count, missing lead time, overdue receipt, or missing historical month remain visible as review cases. Item observations remain unchanged in every scenario. A scenario only changes the projected demand rate, modeled lead time, or effective date of eligible receipts. An overdue receipt is excluded based on the original snapshot date before any hypothetical delay is applied.

## Four separate kinds of information

1. Observed facts: snapshot counts, allocations, monthly usage, and dated PO records. All are fictional here.
2. Calculated projections: demand rate, stock curves, and estimated threshold dates.
3. Recommendations: action, proposed quantity, reason, scenario, review flags, and priority.
4. Human decisions: initialized to `not_recorded`; approval is outside the prototype.

The audit includes inputs and policy values sufficient to recompute each result. The algorithm's versioned source code supplies the implementation. There is no claim of tamper-proof auditing or retention enforcement.

See [project history](project-history.md) for the original Excel workflow and the planned workbook/history/AI-intake extensions; those planned capabilities are separate from the current runtime.
