"""Append-only forecast snapshots and later forecast-versus-actual scoring."""

import json
from calendar import monthrange
from datetime import date
from decimal import Decimal
from pathlib import Path

def _default(value):
    if isinstance(value, (date, Decimal)):
        return value.isoformat() if isinstance(value, date) else format(value, "f")
    raise TypeError(type(value).__name__)


def monthly_forecasts(baseline_rows: list[dict], as_of: date, periods: int = 3) -> list[dict]:
    forecasts = []
    first_month = as_of.replace(day=1)
    for _ in range(periods):
        first_month = date(first_month.year + (first_month.month == 12), first_month.month % 12 + 1, 1)
        days = monthrange(first_month.year, first_month.month)[1]
        for row in baseline_rows:
            daily = row["forecast"]["baseline_daily_usage"]
            if daily is None:
                continue
            item_id = row["item_id"]
            target = first_month.isoformat()
            forecasts.append({
                "forecast_id": f"{as_of.isoformat()}|{item_id}|{target}",
                "forecast_origin": as_of.isoformat(), "item_id": item_id,
                "target_month": target,
                "forecast_quantity": format(daily * days, "f"),
                "forecast_method": row["forecast"]["forecast_method"],
                "history_window_months": row["forecast"]["history_window_months"],
                "forecast_daily_usage": format(daily, "f"),
                "confidence_note": "Input-coverage heuristic; not an accuracy probability.",
            })
    return forecasts


def preserve_forecast_history(path: Path, candidates: list[dict]) -> tuple[list[dict], list[str]]:
    """Keep the first stored value for each forecast_id; never reforecast a saved snapshot."""
    existing = {}
    if path.exists():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not record.get("forecast_id") or record["forecast_id"] in existing:
                raise ValueError(f"Invalid or duplicate forecast history at line {line_number}")
            existing[record["forecast_id"]] = record
    collisions = []
    for candidate in candidates:
        key = candidate["forecast_id"]
        if key in existing:
            if existing[key]["forecast_quantity"] != candidate["forecast_quantity"]:
                collisions.append(key)
            continue
        existing[key] = candidate
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(existing.values(), key=lambda x: (x["forecast_origin"], x["target_month"], x["item_id"]))
    path.write_text("".join(json.dumps(row, default=_default, sort_keys=True) + "\n" for row in ordered),
                    encoding="utf-8", newline="\n")
    return ordered, collisions


def compare_forecasts_to_actuals(history: list[dict], orders: tuple, through: date | None) -> list[dict]:
    actuals = {}
    if through:
        for order in orders:
            month = order.order_date.replace(day=1)
            period_end = date(month.year, month.month, monthrange(month.year, month.month)[1])
            if month <= order.order_date.replace(day=1) and order.order_date <= through and order.status != "cancelled":
                key = order.item_id, month.isoformat()
                actuals[key] = actuals.get(key, Decimal(0)) + order.quantity
    rows = []
    for item in history:
        month = date.fromisoformat(item["target_month"])
        period_end = date(month.year, month.month, monthrange(month.year, month.month)[1])
        actual = actuals.get((item["item_id"], item["target_month"])) if through and period_end <= through else None
        forecast = Decimal(item["forecast_quantity"])
        error = abs(forecast - actual) if actual is not None else None
        percent = (error / abs(actual) * 100) if actual not in (None, Decimal(0)) else None
        direction = "not available" if actual is None else "over" if forecast > actual else "under" if forecast < actual else "even"
        rows.append({**item, "actual_quantity": actual, "absolute_error": error,
                     "percentage_error": percent, "direction": direction,
                     "actual_available_through": through})
    return rows
