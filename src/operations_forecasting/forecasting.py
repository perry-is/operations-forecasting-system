"""Calendar-aware moving average; absent months are not zero-demand months."""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from .models import Usage

PRECISION = Decimal("0.000001")


def month_end(day: date) -> date:
    return day.replace(day=monthrange(day.year, day.month)[1])


def forecast(history: tuple[Usage, ...], as_of: date, window: int = 3) -> dict:
    if window < 1:
        raise ValueError("History window must be positive")
    latest = as_of if as_of == month_end(as_of) else as_of.replace(day=1) - timedelta(days=1)
    months = []
    for _ in range(window):
        months.append(latest.replace(day=1))
        latest = latest.replace(day=1) - timedelta(days=1)
    months.reverse()
    selected = sorted((x for x in history if x.month in months), key=lambda x: x.month)
    flags = []
    if len({x.month for x in selected}) != len(selected):
        raise ValueError("Duplicate usage month")
    if len(selected) < window:
        flags.append("INSUFFICIENT_HISTORY")
    if any(x.quantity < 0 for x in selected):
        flags.append("INVALID_USAGE")
    usable = [x for x in selected if x.quantity >= 0]
    days = sum(monthrange(x.month.year, x.month.month)[1] for x in usable)
    total = sum((x.quantity for x in usable), Decimal(0))
    daily = (total / days).quantize(PRECISION) if days else None
    if len(usable) >= 3:
        prior_rates = [x.quantity / monthrange(x.month.year, x.month.month)[1] for x in usable[:-1]]
        prior = sum(prior_rates) / len(prior_rates)
        last_rate = usable[-1].quantity / monthrange(usable[-1].month.year, usable[-1].month.month)[1]
        if last_rate > 0 and (prior == 0 or last_rate > prior * 3):
            flags.append("DEMAND_ANOMALY")
        if 0 < sum(x.quantity == 0 for x in usable) and any(x.quantity > 0 for x in usable):
            flags.append("INTERMITTENT_DEMAND")
    if flags:
        flags.append("UNCERTAIN_FORECAST")
    return {
        "forecast_method": "calendar_day_moving_average", "history_window_months": window,
        "expected_months": months, "observed_months": [x.month for x in usable],
        "observed_days": days, "observed_usage": total, "baseline_daily_usage": daily,
        "data_quality": "low" if flags else "adequate_history",
        "quality_meaning": "Input coverage and heuristic checks; not a probability of forecast accuracy",
        "review_flags": flags,
    }
