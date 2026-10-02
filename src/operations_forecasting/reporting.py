"""Readable decisions and inspectable JSON; no purchase execution."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path


def json_default(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Unsupported output type: {type(value).__name__}")


def summary(records: list[dict]) -> dict:
    actionable = [r for r in records if r["recommendation"]["action"] in {"ORDER", "EXPEDITE"}]
    priced = [r for r in actionable if r["observed_facts"]["unit_cost"] is not None]
    return {
        "items_evaluated": len(records),
        "projected_shortages": sum(bool(r["projection"] and r["projection"]["stockout_date"]) for r in records),
        "recommended_orders": sum(r["recommendation"]["action"] == "ORDER" for r in records),
        "expedite_candidates": sum(r["recommendation"]["candidate_action"] == "EXPEDITE" for r in records),
        "excess_stock_review_items": sum(bool(r["recommendation"]["excess_stock"]) for r in records),
        "unavailable_projections": sum(r["projection"] is None for r in records),
        "unknown_lead_time_risk_items": sum(r["recommendation"]["lead_time_risk"] is None for r in records),
        "outstanding_inbound_issues": sum(any(p["exclusion_reason"] in {"OVERDUE_PURCHASE_ORDER", "MISSING_RECEIPT_DATE", "INVALID_PO_QUANTITY"} for p in r["inbound_evaluations"]) for r in records),
        "data_quality_review_items": sum(bool(r["recommendation"]["review_flags"]) for r in records),
        "suggested_purchase_value": sum((r["observed_facts"]["unit_cost"] * r["recommendation"]["suggested_quantity"] for r in priced), Decimal(0)).quantize(Decimal("0.01")),
        "unpriced_actionable_items": len(actionable) - len(priced),
    }


def display_quantity(value: Decimal | None) -> str:
    """Round to one decimal place for display only; stored values keep full precision."""
    if value is None:
        return "unknown"
    return format(value.quantize(Decimal("0.1")).normalize(), "f")


def render_report(result: dict) -> str:
    records = result["recommendations"]
    baseline = [r for r in records if r["scenario"] == "BASELINE"]
    lines = ["# Synthetic Operations Planning Report", "", f"Snapshot close: {result['as_of']}. All records and costs are fictional.", "",
             "Recommendations are proposals. No human approval is recorded and no order is placed.", "",
             "## Baseline overview", ""]
    for key, value in summary(baseline).items():
        lines.append(f"- {key.replace('_', ' ').capitalize()}: {value}")
    lines += ["", "Purchase value is in fictional currency units and covers ORDER and EXPEDITE quantities with known costs; HUMAN REVIEW candidates are excluded.",
              "Shortages are measured before any proposed new purchase. Expedite candidates include tentative candidates awaiting data review.", "",
              "## Item recommendations", "", "| Item | Priority | Available | At lead time | Stockout | Action | Quantity | Review flags |",
              "|---|---:|---:|---:|---|---|---:|---|"]
    for r in sorted(baseline, key=lambda r: (-r["recommendation"]["priority"], r["item_id"])):
        rec, p = r["recommendation"], r["projection"]
        stock = (str(p["stockout_date"]) if p["stockout_date"] else "none in horizon") if p else "unknown"
        available = r["observed_facts"]["current_on_hand"] - r["observed_facts"]["allocated_quantity"]
        lead_stock = display_quantity(p["projected_stock_at_lead_time"] if p else None)
        lines.append(f"| {r['item_id']} | {rec['priority']} | {display_quantity(available)} | {lead_stock} | {stock} | {rec['action']} | {rec['suggested_quantity'] if rec['suggested_quantity'] is not None else 'withheld'} | {', '.join(rec['review_flags']) or 'none'} |")
    lines += ["", "## Scenario comparisons", "", "Same source snapshot; only stated scenario assumptions change. Detailed projections and reasons are in recommendations.json.", "",
              "| Item | " + " | ".join(result["scenario_names"]) + " |",
              "|---|" + "---|" * len(result["scenario_names"])]
    lookup = {(r["scenario"], r["item_id"]): r for r in records}
    for base in baseline:
        cells = []
        for name in result["scenario_names"]:
            rec = lookup[name, base["item_id"]]["recommendation"]
            label = rec["action"]
            if label == "HUMAN REVIEW":
                label += (f" ({rec['candidate_action']}; candidate {rec['candidate_quantity']})"
                          if rec["candidate_quantity"] is not None else " (no reliable quantity)")
            elif rec["suggested_quantity"]:
                label += f" {rec['suggested_quantity']}"
            cells.append(label)
        lines.append(f"| {base['item_id']} | " + " | ".join(cells) + " |")
    lines += ["", "## Review procedure", "", "Confirm counts, allocations, demand changes, and PO dates before deciding. Resolve flagged inputs and rerun; record approvals in the operational system outside this prototype.",
              "Do not treat an excess flag as authorization to dispose of stock. Unknown lead time or absent history means no reliable order quantity."]
    return "\n".join(lines) + "\n"


def write_outputs(result: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    public = {key: value for key, value in result.items() if key != "audit"}
    (directory / "recommendations.json").write_text(json.dumps(public, default=json_default, indent=2) + "\n", encoding="utf-8", newline="\n")
    (directory / "audit.jsonl").write_text("\n".join(json.dumps(x, default=json_default, sort_keys=True) for x in result["audit"]) + "\n", encoding="utf-8", newline="\n")
    (directory / "planning_report.md").write_text(render_report(result), encoding="utf-8", newline="\n")
