# Synthetic Operations Planning Report

Snapshot close: 2026-06-30. All records and costs are fictional.

Recommendations are proposals. No human approval is recorded and no order is placed.

## Baseline overview

- Items evaluated: 14
- Projected shortages: 11
- Recommended orders: 1
- Expedite candidates: 3
- Excess stock review items: 2
- Unavailable projections: 0
- Unknown lead time risk items: 1
- Outstanding inbound issues: 2
- Data quality review items: 5
- Suggested purchase value: 2517.00
- Unpriced actionable items: 0

Purchase value is in fictional currency units and covers ORDER and EXPEDITE quantities with known costs; HUMAN REVIEW candidates are excluded.
Shortages are measured before any proposed new purchase. Expedite candidates include tentative candidates awaiting data review.

## Item recommendations

| Item | Priority | Available | At lead time | Stockout | Action | Quantity | Review flags |
|---|---:|---:|---:|---|---|---:|---|
| PART-010 | 4 | 25 | -3 | 2026-07-13 | EXPEDITE | 83 | none |
| KIT-002 | 3 | -4 | unknown | 2026-06-30 | HUMAN REVIEW | withheld | INCONSISTENT_QUANTITIES, MISSING_RECEIPT_DATE, STALE_COUNT, UNKNOWN_LEAD_TIME |
| PART-003 | 3 | 100 | -20 | 2026-08-03 | EXPEDITE | 200 | none |
| PART-005 | 3 | 10 | -11 | 2026-07-11 | HUMAN REVIEW | withheld | OVERDUE_PURCHASE_ORDER |
| PART-001 | 2 | 110 | 96 | none in horizon | NO ACTION | 0 | none |
| PART-002 | 2 | 90 | 20 | 2026-08-15 | ORDER | 90 | none |
| PART-004 | 2 | 25 | 55 | 2026-09-24 | MONITOR | 0 | none |
| PART-007 | 2 | 60 | 4.4 | 2026-07-23 | HUMAN REVIEW | withheld | DEMAND_ANOMALY, UNCERTAIN_FORECAST |
| PART-009 | 2 | 20 | 6 | 2026-07-21 | HUMAN REVIEW | withheld | INSUFFICIENT_HISTORY, UNCERTAIN_FORECAST |
| PART-011 | 2 | 52 | 22 | 2026-08-22 | MONITOR | 0 | none |
| PART-012 | 2 | 60 | 25 | 2026-08-30 | MONITOR | 0 | none |
| KIT-001 | 1 | 90 | 120 | none in horizon | REDUCE / REVIEW EXCESS | 0 | none |
| PART-006 | 1 | 15 | 12.2 | 2026-09-14 | HUMAN REVIEW | withheld | INTERMITTENT_DEMAND, UNCERTAIN_FORECAST |
| PART-008 | 1 | 500 | 483.7 | none in horizon | REDUCE / REVIEW EXCESS | 0 | none |

## Scenario comparisons

Same source snapshot; only stated scenario assumptions change. Detailed projections and reasons are in recommendations.json.

| Item | BASELINE | DEMAND +20% | LEAD TIME +14 DAYS | INBOUND PO DELAYED |
|---|---|---|---|---|
| PART-001 | NO ACTION | MONITOR | NO ACTION | NO ACTION |
| PART-002 | ORDER 90 | ORDER 104 | EXPEDITE 118 | ORDER 90 |
| PART-003 | EXPEDITE 200 | EXPEDITE 224 | EXPEDITE 242 | EXPEDITE 200 |
| PART-004 | MONITOR | MONITOR | MONITOR | EXPEDITE 85 |
| PART-005 | HUMAN REVIEW (EXPEDITE; candidate 61) | HUMAN REVIEW (EXPEDITE; candidate 66) | HUMAN REVIEW (EXPEDITE; candidate 75) | HUMAN REVIEW (EXPEDITE; candidate 61) |
| PART-006 | HUMAN REVIEW (MONITOR; candidate 0) | HUMAN REVIEW (MONITOR; candidate 0) | HUMAN REVIEW (MONITOR; candidate 0) | HUMAN REVIEW (MONITOR; candidate 0) |
| PART-007 | HUMAN REVIEW (ORDER; candidate 96) | HUMAN REVIEW (EXPEDITE; candidate 107) | HUMAN REVIEW (EXPEDITE; candidate 133) | HUMAN REVIEW (ORDER; candidate 96) |
| PART-008 | REDUCE / REVIEW EXCESS | REDUCE / REVIEW EXCESS | REDUCE / REVIEW EXCESS | REDUCE / REVIEW EXCESS |
| PART-009 | HUMAN REVIEW (ORDER; candidate 44) | HUMAN REVIEW (ORDER; candidate 47) | HUMAN REVIEW (EXPEDITE; candidate 58) | HUMAN REVIEW (ORDER; candidate 44) |
| PART-010 | EXPEDITE 83 | EXPEDITE 89 | EXPEDITE 111 | EXPEDITE 83 |
| PART-011 | MONITOR | ORDER 44 | ORDER 52 | MONITOR |
| PART-012 | MONITOR | ORDER 52 | ORDER 59 | MONITOR |
| KIT-001 | REDUCE / REVIEW EXCESS | REDUCE / REVIEW EXCESS | REDUCE / REVIEW EXCESS | REDUCE / REVIEW EXCESS |
| KIT-002 | HUMAN REVIEW (no reliable quantity) | HUMAN REVIEW (no reliable quantity) | HUMAN REVIEW (no reliable quantity) | HUMAN REVIEW (no reliable quantity) |

## Review procedure

Confirm counts, allocations, demand changes, and PO dates before deciding. Resolve flagged inputs and rerun; record approvals in the operational system outside this prototype.
Do not treat an excess flag as authorization to dispose of stock. Unknown lead time or absent history means no reliable order quantity.
