"""Planning rules produce proposals, never approvals or purchase orders."""

from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING

from .models import Item

PRIORITY = {"low": 1, "normal": 2, "high": 3, "critical": 4}


def item_flags(item: Item, as_of: date) -> list[str]:
    flags = []
    if item.current_on_hand < 0:
        flags.append("NEGATIVE_INVENTORY")
    if item.allocated_quantity < 0 or item.allocated_quantity > item.current_on_hand:
        flags.append("INCONSISTENT_QUANTITIES")
    if item.minimum_stock < 0 or item.target_stock < item.minimum_stock:
        flags.append("INVALID_STOCK_POLICY")
    if item.supplier_lead_time_days is None:
        flags.append("UNKNOWN_LEAD_TIME")
    elif item.supplier_lead_time_days < 1:
        flags.append("INVALID_LEAD_TIME")
    if (as_of - item.last_updated).days > 30:
        flags.append("STALE_COUNT")
    if item.last_updated > as_of:
        flags.append("FUTURE_COUNT_DATE")
    if item.unit_cost is not None and item.unit_cost < 0:
        flags.append("INVALID_UNIT_COST")
    if item.criticality not in PRIORITY:
        flags.append("UNKNOWN_CRITICALITY")
    return flags


def ceiling(value: Decimal) -> int:
    return int(max(Decimal(0), value).to_integral_value(rounding=ROUND_CEILING))


def recommend(item: Item, projection: dict | None, daily: Decimal | None,
              lead_days: int | None, as_of: date, flags: list[str], review_days: int = 7) -> dict:
    action, reason, quantity, order_by = "HUMAN REVIEW", "A forecast and positive lead time are required for purchasing calculations.", None, None
    basis = {}
    excess = None
    if projection is not None:
        excess_limit = max(item.target_stock * Decimal("1.5"), daily * projection["horizon_days"] * 2)
        supply = projection["current_available"] + projection["confirmed_inbound_within_horizon"]
        excess = supply > excess_limit
        basis.update({"excess_supply_basis": supply, "excess_threshold": excess_limit})
    if projection is not None and lead_days is not None:
        balances = projection["daily_balances"]
        arrival = as_of + timedelta(days=lead_days)
        minimum_until_next_review_arrival = min(balances[:lead_days + review_days + 1])
        stockout = projection["stockout_date"]
        target = max(item.target_stock, projection["safety_threshold"] + daily * review_days)
        target_gap = max(Decimal(0), target - projection["projected_stock_at_lead_time"])
        bridge_gap = max(Decimal(0), -min(balances[:lead_days]))
        basis.update({"effective_target_on_arrival": target, "target_gap": target_gap,
                      "bridge_shortfall_before_arrival": bridge_gap, "rounding": "ceil to whole units",
                      "review_cycle_days": review_days,
                      "minimum_until_next_review_arrival": minimum_until_next_review_arrival})
        quantity = 0
        if stockout is not None and stockout < arrival:
            action = "EXPEDITE"
            quantity = ceiling(max(target_gap, bridge_gap))
            reason = "Projected stockout precedes a new standard-lead-time receipt; review faster supply or a demand adjustment."
        elif minimum_until_next_review_arrival < projection["safety_threshold"] and target_gap > 0:
            action = "ORDER"
            quantity = ceiling(target_gap)
            reason = "Projected stock falls below safety stock before an order placed at the next review could arrive."
        elif minimum_until_next_review_arrival < projection["safety_threshold"]:
            action = "MONITOR"
            reason = "Confirmed inbound meets the arrival target; monitor the temporary safety-stock dip instead of proposing a zero-quantity order."
        elif excess:
            action = "REDUCE / REVIEW EXCESS"
            reason = "Available stock plus eligible horizon inbound exceeds the documented excess threshold; review future buying, not automatic disposal."
        elif projection["below_safety_date"] is not None:
            action = "MONITOR"
            reason = "A later safety-stock crossing is projected, beyond the current lead-time and review-cycle trigger."
        else:
            action = "NO ACTION"
            reason = "The dated projection stays above safety stock and below the excess threshold."
        if projection["below_safety_date"] is not None:
            order_by = projection["below_safety_date"] - timedelta(days=lead_days)
    return {
        "action": "HUMAN REVIEW" if flags else action, "candidate_action": action,
        "suggested_quantity": None if flags else quantity, "candidate_quantity": quantity,
        "reason": reason, "quantity_calculation": basis,
        "lead_time_days": lead_days,
        "earliest_standard_receipt_date": as_of + timedelta(days=lead_days) if lead_days is not None else None,
        "suggested_order_by": order_by, "excess_stock": excess,
        "lead_time_risk": (projection["stockout_date"] is not None
                           and projection["stockout_date"] < as_of + timedelta(days=lead_days))
                          if projection is not None and lead_days is not None else None,
        "review_required": bool(flags) or bool(excess) or action in {"EXPEDITE", "REDUCE / REVIEW EXCESS", "HUMAN REVIEW"},
        "review_flags": sorted(set(flags)), "priority": PRIORITY.get(item.criticality, 2),
        "human_decision": {"status": "not_recorded", "approved_quantity": None},
    }
