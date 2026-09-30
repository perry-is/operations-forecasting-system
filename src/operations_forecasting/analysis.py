"""Historical order, shipping, demand, and recurring-pattern summaries."""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from statistics import pstdev

from .models import DataSet


def _week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def historical_analysis(data: DataSet, as_of: date) -> dict[str, list[dict]]:
    orders = [o for o in data.orders if o.order_date <= (data.actuals_through or as_of) and o.status != "cancelled"]
    shipments = [s for s in data.shipments if s.ship_date <= (data.actuals_through or as_of)]
    weekly = defaultdict(lambda: {"order_count": 0, "ordered_quantity": Decimal(0), "shipped_quantity": Decimal(0), "order_value": Decimal(0)})
    monthly = defaultdict(lambda: {"order_count": 0, "ordered_quantity": Decimal(0), "shipped_quantity": Decimal(0), "order_value": Decimal(0)})
    customer_category = defaultdict(lambda: {"order_count": 0, "ordered_quantity": Decimal(0), "order_value": Decimal(0), "item_count": 0})
    demand = defaultdict(Decimal)
    for o in orders:
        week, month = _week_start(o.order_date), o.order_date.replace(day=1)
        value = o.quantity * o.unit_price
        for key, group in ((week, weekly), (month, monthly)):
            group[key]["order_count"] += 1
            group[key]["ordered_quantity"] += o.quantity
            group[key]["order_value"] += value
        customer_category[o.customer, o.category]["order_count"] += 1
        customer_category[o.customer, o.category]["ordered_quantity"] += o.quantity
        customer_category[o.customer, o.category]["order_value"] += value
        customer_category[o.customer, o.category]["item_count"] += 1
        demand[o.item_id, month] += o.quantity
    for s in shipments:
        weekly[_week_start(s.ship_date)]["shipped_quantity"] += s.quantity
        monthly[s.ship_date.replace(day=1)]["shipped_quantity"] += s.quantity

    monthly_rows = []
    for month, values in sorted(monthly.items()):
        monthly_rows.append({"month": month, **values,
                             "average_order_quantity": values["ordered_quantity"] / values["order_count"] if values["order_count"] else Decimal(0)})
    progression = defaultdict(list)
    for row in monthly_rows:
        progression["overall"].append(row["ordered_quantity"])
    recurring = []
    for item in data.items:
        series = [demand[item.item_id, month] for month in sorted({m for item_id, m in demand if item_id == item.item_id})]
        if len(series) >= 3 and len(set(series)) == 1:
            recurring.append({"item_id": item.item_id, "pattern": "stable monthly demand", "months_observed": len(series), "predictability": "repeatable in observed history"})
        elif len(series) >= 3:
            mean = sum(series, Decimal(0)) / len(series)
            cv = Decimal(str(pstdev(float(x) for x in series))) / mean if mean else None
            recurring.append({"item_id": item.item_id, "pattern": "variable or changing monthly demand", "months_observed": len(series),
                              "predictability": "more repeatable" if cv is not None and cv < Decimal("0.35") else "limited by variation"})
    all_months = sorted({m for _, m in demand})
    demand_rows = [{"item_id": item.item_id, "month": month, "ordered_quantity": demand[item.item_id, month]}
                   for item in data.items for month in all_months if (item.item_id, month) in demand]
    return {
        "weekly": [{"week_start": key, **value} for key, value in sorted(weekly.items())],
        "monthly": monthly_rows,
        "customer_category": [{"customer": customer, "category": category, **value}
                              for (customer, category), value in sorted(customer_category.items())],
        "inventory_demand": demand_rows,
        "recurring_patterns": recurring,
    }
