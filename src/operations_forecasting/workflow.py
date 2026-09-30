"""Pure scenario planning over immutable records."""

from dataclasses import asdict
from datetime import date
from decimal import Decimal

from .forecasting import PRECISION, forecast
from .ingest import check_records
from .inventory import inspect_inbound, project
from .models import DataSet, Scenario
from .purchasing import item_flags, recommend

SCENARIOS = (
    Scenario(),
    Scenario("DEMAND +20%", demand_multiplier=Decimal("1.2")),
    Scenario("LEAD TIME +14 DAYS", lead_time_extra_days=14),
    Scenario("INBOUND PO DELAYED", inbound_delay_days=21),
)


def plan(data: DataSet, as_of: date, scenarios: tuple[Scenario, ...] = SCENARIOS,
         horizon_days: int = 90, safety_factor: Decimal = Decimal("1.25")) -> dict:
    check_records(data)
    if horizon_days < 1 or not safety_factor.is_finite() or safety_factor < 1:
        raise ValueError("Positive horizon and finite safety factor >= 1 are required")
    if len({s.name for s in scenarios}) != len(scenarios):
        raise ValueError("Scenario names must be unique")
    records, audit = [], []
    for scenario in scenarios:
        for item in data.items:
            history = tuple(x for x in data.usage if x.item_id == item.item_id)
            orders = tuple(x for x in data.purchase_orders if x.item_id == item.item_id)
            predicted = forecast(history, as_of)
            flags = item_flags(item, as_of) + predicted["review_flags"]
            inbound, po_flags = inspect_inbound(orders, as_of, scenario)
            flags += po_flags
            lead = item.supplier_lead_time_days
            lead = lead + scenario.lead_time_extra_days if lead is not None and lead > 0 else None
            horizon = max(horizon_days, lead + 7 if lead is not None else 0)
            daily = predicted["baseline_daily_usage"]
            daily = (daily * scenario.demand_multiplier).quantize(PRECISION) if daily is not None else None
            predicted = {**predicted, "forecast_daily_usage": daily, "forecast_period_days": horizon,
                         "forecast_period_usage": daily * horizon if daily is not None else None}
            projection = project(item, daily, inbound, as_of, horizon, lead, safety_factor) if daily is not None else None
            recommendation = recommend(item, projection, daily, lead, as_of, flags)
            summary = {k: v for k, v in projection.items() if k != "daily_balances"} if projection else None
            record = {"item_id": item.item_id, "description": item.description, "scenario": scenario.name,
                      "observed_facts": asdict(item), "forecast": predicted, "projection": summary,
                      "inbound_evaluations": inbound, "recommendation": recommendation}
            records.append(record)
            audit.append({"schema_version": "1.0", "as_of": as_of, "item_id": item.item_id,
                          "scenario": asdict(scenario), "source_values": {"item": asdict(item),
                          "usage": [asdict(x) for x in history], "purchase_orders": [asdict(x) for x in orders]},
                          "policy": {"safety_factor": safety_factor, "base_horizon_days": horizon_days,
                          "review_cycle_days": 7, "forecast_rounding_decimal_places": 6},
                          "forecast": predicted, "projected_inventory": summary,
                          "inbound_supply_considered": inbound, "recommendation": recommendation})
    return {"schema_version": "1.0", "synthetic": True, "as_of": as_of,
            "scenario_names": [s.name for s in scenarios], "recommendations": records, "audit": audit}
