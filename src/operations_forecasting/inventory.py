"""Dated inbound supply and daily projections; inbound is never on-hand stock."""

from datetime import date, timedelta
from decimal import Decimal

from .models import Item, PurchaseOrder, Scenario


def inspect_inbound(orders: tuple[PurchaseOrder, ...], as_of: date, scenario: Scenario) -> tuple[list[dict], list[str]]:
    evaluations, flags = [], []
    for po in orders:
        reason = None
        due = po.expected_receipt_date
        if po.status != "confirmed":
            reason = f"status_{po.status}"
        elif po.quantity <= 0:
            reason = "INVALID_PO_QUANTITY"
        elif due is None:
            reason = "MISSING_RECEIPT_DATE"
        elif due <= as_of:
            reason = "OVERDUE_PURCHASE_ORDER"
        if reason in {"INVALID_PO_QUANTITY", "MISSING_RECEIPT_DATE", "OVERDUE_PURCHASE_ORDER"}:
            flags.append(reason)
        evaluations.append({
            "po_reference": po.po_reference, "quantity": po.quantity, "status": po.status,
            "observed_receipt_date": due,
            "effective_receipt_date": due + timedelta(days=scenario.inbound_delay_days) if due else None,
            "eligible": reason is None, "exclusion_reason": reason,
        })
    return evaluations, flags


def project(item: Item, daily: Decimal, inbound: list[dict], as_of: date,
            horizon: int, lead_days: int | None, safety_factor: Decimal) -> dict:
    available = item.current_on_hand - item.allocated_quantity
    balance = available
    safety = item.minimum_stock * safety_factor
    risks = {"stockout_date": None, "below_minimum_date": None, "below_safety_date": None}
    thresholds = {"stockout_date": Decimal(0), "below_minimum_date": item.minimum_stock, "below_safety_date": safety}
    balances = [available]
    for key, threshold in thresholds.items():
        if available < threshold:
            risks[key] = as_of
    receipts = {}
    for po in inbound:
        if po["eligible"]:
            due = po["effective_receipt_date"]
            receipts[due] = receipts.get(due, Decimal(0)) + po["quantity"]
    for offset in range(1, horizon + 1):
        day = as_of + timedelta(days=offset)
        balance += receipts.get(day, Decimal(0)) - daily
        balances.append(balance)
        for key, threshold in thresholds.items():
            if risks[key] is None and balance < threshold:
                risks[key] = day
    return {
        "current_on_hand": item.current_on_hand, "allocated_quantity": item.allocated_quantity,
        "current_available": available, "safety_threshold": safety,
        "horizon_days": horizon, "horizon_date": as_of + timedelta(days=horizon),
        "confirmed_inbound_within_horizon": sum((v for d, v in receipts.items() if as_of < d <= as_of + timedelta(days=horizon)), Decimal(0)),
        "confirmed_inbound_by_lead_time": sum((v for d, v in receipts.items() if lead_days is not None and as_of < d <= as_of + timedelta(days=lead_days)), Decimal(0)),
        "projected_available_at_horizon": balance,
        "projected_stock_at_lead_time": balances[lead_days] if lead_days is not None else None,
        "minimum_projected_available": min(balances),
        **risks, "daily_balances": balances,
    }
