# Forecasting and purchasing method

## Calendar and demand

The snapshot is the close of June 30, 2026. Projection day one is July 1. History consists of monthly totals, with a month represented by its first day. A mid-month snapshot uses the most recent completed month; a month-end snapshot includes the month just closed.

For the three-month window:

`baseline_daily_usage = sum(usable observed usage) / sum(days in usable observed months)`

`scenario_daily_usage = baseline_daily_usage × scenario demand multiplier`

`forecast_period_usage = scenario_daily_usage × projection horizon days`

Daily rates are rounded to six decimal places before projections. Absent months are not interpreted as zero usage; explicitly recorded zero months are used. Missing history and invalid negative usage produce review flags. With no usable history, the forecast and projection are unavailable. Sparse history may produce a tentative rate using observed days, but the order-ready quantity is withheld.

A positive latest-month daily rate over three times the preceding observed daily-rate average flags an anomaly. A mixture of zero and positive months flags intermittency. These are simple heuristics, not statistical confidence intervals. Rising and declining data affect the rolling average; the prototype does not extrapolate a fitted trend.

## Inventory and supply

`current_available = current_on_hand - allocated_quantity`

`balance[d] = balance[d-1] + eligible receipts on date d - scenario_daily_usage`

Allocations represent committed stock already removed from availability. Synthetic forecast demand is additional, unallocated usage. If a real forecast included the same allocated orders, this formula would double-count demand; that boundary would require reconciliation before operational use.

The PO receipt occurs before that date's daily consumption. Open confirmed receipts due on or before the snapshot close are overdue and excluded, not rolled into on hand. Other excluded records are received, cancelled, unconfirmed, missing dates, or nonpositive quantities. A receipt beyond the horizon stays visible in audit but does not inflate that horizon's available stock.

The horizon is 90 calendar days by default, extended if needed to include lead time plus a seven-day review cycle. All default demo scenarios use 90 days. Projections are not clamped at zero: a negative balance exposes modeled unmet demand, even if a later receipt restores stock. Threshold dates retain the first crossing, so late inbound cannot hide an earlier shortage.

## Risk and purchasing

`safety_threshold = minimum_stock × safety_factor` (default factor 1.25)

Crossings are strictly below zero, minimum, and safety. Zero itself is depleted but not yet a shortage under the daily model. A shortage on the new receipt date can be covered by an order arriving at its start; shortage before that date requires an expedite review.

`effective_target = max(target_stock, safety_threshold + 7 × daily_usage)`

`target_gap = max(0, effective_target - projected_stock_at_lead_time)`

`bridge_shortfall = max(0, -minimum projected balance before new standard receipt)`

ORDER quantity is the target gap rounded upward to a whole unit. EXPEDITE candidate quantity is the greater of target gap and bridge shortfall, rounded upward. These are hypothetical buying quantities, not pack-size or supplier-constrained orders. An expedite candidate means ordinary lead time is inadequate and requires a person to assess faster supply or altered demand.

The reorder trigger examines the minimum balance from now through lead time plus seven days. A safety crossing in that period creates an order proposal when the target gap is positive. Confirmed inbound that meets the arrival target can instead create a monitoring recommendation; the engine does not create zero-quantity orders. A suggested order-by date is the first projected safety crossing minus lead time, and may already be past.

Excess compares current available plus eligible horizon inbound against `max(1.5 × target_stock, 2 × horizon demand)`. Shortage urgency takes precedence over excess when both occur; the independent excess flag remains visible. A large late receipt can therefore coexist with an earlier shortage.

These configurable policies are newly constructed public-demo rules, not a verbatim reconstruction of private workplace procedures. They require operational review before any real use.
