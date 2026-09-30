"""CSV ingestion rejects ambiguous IDs and malformed values before planning."""

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from .models import DataSet, Item, PurchaseOrder, Usage


def number(value: str) -> Decimal:
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError("Quantities and costs must be finite")
    return result


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_data(directory: Path) -> DataSet:
    items = tuple(Item(
        item_id=r["item_id"], description=r["description"], category=r["category"],
        current_on_hand=number(r["current_on_hand"]), allocated_quantity=number(r["allocated_quantity"]),
        minimum_stock=number(r["minimum_stock"]), target_stock=number(r["target_stock"]),
        supplier_lead_time_days=int(r["supplier_lead_time_days"]) if r["supplier_lead_time_days"] else None,
        unit_cost=number(r["unit_cost"]) if r["unit_cost"] else None,
        criticality=r["criticality"], last_updated=date.fromisoformat(r["last_updated"]),
    ) for r in rows(directory / "synthetic_items.csv"))
    usage = tuple(Usage(r["item_id"], date.fromisoformat(r["month"]), number(r["quantity"]))
                  for r in rows(directory / "synthetic_usage.csv"))
    orders = tuple(PurchaseOrder(
        r["po_reference"], r["item_id"], number(r["quantity"]),
        date.fromisoformat(r["expected_receipt_date"]) if r["expected_receipt_date"] else None,
        r["status"],
    ) for r in rows(directory / "synthetic_purchase_orders.csv"))
    check_records(DataSet(items, usage, orders))
    return DataSet(items, usage, orders)


def check_records(data: DataSet) -> None:
    for label, keys in (
        ("item", [x.item_id for x in data.items]),
        ("usage month", [(x.item_id, x.month) for x in data.usage]),
        ("PO reference", [x.po_reference for x in data.purchase_orders]),
    ):
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate {label}; resolve before planning")
    item_ids = {x.item_id for x in data.items}
    if any(x.item_id not in item_ids for x in (*data.usage, *data.purchase_orders)):
        raise ValueError("Usage or PO references an unknown item")
    if any(x.month.day != 1 for x in data.usage):
        raise ValueError("Usage month must be its first calendar day")
    if any(x.status not in {"confirmed", "unconfirmed", "received", "cancelled"} for x in data.purchase_orders):
        raise ValueError("Unknown PO status; resolve before planning")
