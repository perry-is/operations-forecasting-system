# Decision boundaries

The engine proposes NO ACTION, MONITOR, ORDER, EXPEDITE, REDUCE / REVIEW EXCESS, or HUMAN REVIEW. It never creates purchase orders, changes stock, contacts a supplier, or approves a decision.

Data-quality flags include INSUFFICIENT_HISTORY, UNCERTAIN_FORECAST, DEMAND_ANOMALY, INTERMITTENT_DEMAND, STALE_COUNT, UNKNOWN_LEAD_TIME, OVERDUE_PURCHASE_ORDER, MISSING_RECEIPT_DATE, INVALID_PO_QUANTITY, NEGATIVE_INVENTORY, and INCONSISTENT_QUANTITIES. Invalid policies, lead times, unit costs, count dates, or criticality also produce review flags.

Any such flag makes the action HUMAN REVIEW and withholds `suggested_quantity`. A separate `candidate_action` and `candidate_quantity` expose what the calculation would suggest for investigation. Missing lead time or absent usable history prevents even that quantity calculation. The purchase-value total excludes these withheld candidates.

Unavailable risk assessments use null values, not false: lead-time risk is unknown without a usable projection and lead time; excess risk is unknown without a projection. The report counts unavailable projections and unknown lead-time assessments separately from detected risks.

Criticality affects priority (low 1, normal 2, high 3, critical 4), without changing the forecast, balances, or arithmetic. Expedite and excess recommendations require review even with adequate input coverage. Every purchasing proposal still needs human authorization; `review_required=false` does not grant permission to buy.

The synthetic public workflow calculates simple forecast-versus-actual errors when a full target month is available, but this is a demo measure rather than a validated service level or business-impact result. The original operational workflow has no formal measured outcomes, and this project makes no accuracy, savings, workload, sales, stockout-prevention, or productivity claims for it. Forecast history and forecast-versus-actual are implemented in the public rebuild. Authorized document intake remains a future design extension documented in project-history.md.
