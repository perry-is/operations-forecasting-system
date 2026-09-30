import copy
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal as D
from pathlib import Path

from operations_forecasting.demo import AS_OF, ROOT
from operations_forecasting.forecasting import forecast
from operations_forecasting.ingest import check_records, load_data, number
from operations_forecasting.models import DataSet, PurchaseOrder, Scenario, Usage
from operations_forecasting.reporting import render_report, summary, write_outputs
from operations_forecasting.workflow import plan


class PlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data(ROOT / "examples")
        cls.result = plan(cls.data, AS_OF)
        cls.index = {(r["scenario"], r["item_id"]): r for r in cls.result["recommendations"]}

    def row(self, item_id="PART-001", scenario="BASELINE"):
        return self.index[scenario, item_id]

    def one(self, item, orders=(), history=None):
        if history is None:
            history = tuple(x for x in self.data.usage if x.item_id == item.item_id)
        return plan(DataSet((item,), history, orders), AS_OF, (Scenario(),))["recommendations"][0]

    def test_moving_average_uses_observed_calendar_days(self):
        f = self.row()["forecast"]
        self.assertEqual(f["observed_days"], 91)
        self.assertEqual(f["observed_usage"], D(91))
        self.assertEqual(f["forecast_daily_usage"], D(1))
        self.assertEqual(f["forecast_period_usage"], D(90))

    def test_inventory_position_and_allocations(self):
        p = self.row()["projection"]
        self.assertEqual(p["current_on_hand"], D(120))
        self.assertEqual(p["current_available"], D(110))
        self.assertEqual(p["projected_stock_at_lead_time"], D(96))
        self.assertEqual(p["projected_available_at_horizon"], D(20))

    def test_allocation_change_does_not_change_forecast(self):
        item = self.data.items[0]
        a, b = self.one(item), self.one(replace(item, allocated_quantity=D(20)))
        self.assertEqual(a["forecast"], b["forecast"])
        self.assertEqual(a["projection"]["current_available"] - b["projection"]["current_available"], D(10))

    def test_inbound_prevents_false_reorder_without_becoming_on_hand(self):
        row = self.row("PART-004")
        self.assertEqual(row["projection"]["current_on_hand"], D(25))
        self.assertEqual(row["projection"]["confirmed_inbound_by_lead_time"], D(60))
        self.assertEqual(row["projection"]["projected_stock_at_lead_time"], D(55))
        self.assertEqual(row["recommendation"]["action"], "MONITOR")
        item = next(x for x in self.data.items if x.item_id == "PART-004")
        self.assertEqual(self.one(item)["recommendation"]["action"], "EXPEDITE")

    def test_overdue_po_is_excluded_and_quantity_withheld(self):
        row = self.row("PART-005")
        self.assertEqual(row["projection"]["confirmed_inbound_within_horizon"], 0)
        self.assertIn("OVERDUE_PURCHASE_ORDER", row["recommendation"]["review_flags"])
        self.assertEqual(row["recommendation"]["action"], "HUMAN REVIEW")
        self.assertIsNone(row["recommendation"]["suggested_quantity"])

    def test_currently_healthy_stock_can_run_out_during_lead_time(self):
        row = self.row("PART-003")
        self.assertEqual(row["projection"]["current_available"], D(100))
        self.assertEqual(row["projection"]["projected_stock_at_lead_time"], D(-20))
        self.assertEqual(row["recommendation"]["action"], "EXPEDITE")
        self.assertEqual(row["recommendation"]["suggested_quantity"], 200)
        self.assertTrue(row["recommendation"]["lead_time_risk"])

    def test_reorder_trigger_and_order_quantity_are_explainable(self):
        row = self.row("PART-002")
        self.assertEqual(row["forecast"]["forecast_daily_usage"], D(2))
        self.assertEqual(row["projection"]["projected_stock_at_lead_time"], D(20))
        self.assertEqual(row["recommendation"]["action"], "ORDER")
        self.assertEqual(row["recommendation"]["suggested_quantity"], 90)
        self.assertEqual(row["recommendation"]["quantity_calculation"]["target_gap"], D(90))

    def test_stable_healthy_item_needs_no_action(self):
        self.assertEqual(self.row()["recommendation"]["action"], "NO ACTION")
        self.assertIsNone(self.row()["projection"]["stockout_date"])

    def test_stockout_is_strictly_below_zero(self):
        self.assertEqual(self.row("PART-003")["projection"]["stockout_date"], date(2026, 8, 3))
        self.assertEqual(self.row("PART-011")["projection"]["stockout_date"], date(2026, 8, 22))

    def test_risk_threshold_dates_are_distinct(self):
        p = self.row("PART-011")["projection"]
        self.assertEqual(p["below_safety_date"], date(2026, 8, 9))
        self.assertEqual(p["below_minimum_date"], date(2026, 8, 12))
        self.assertLess(p["below_minimum_date"], p["stockout_date"])

    def test_sparse_history_is_not_padded_with_zero_months(self):
        row = self.row("PART-009")
        self.assertEqual(row["forecast"]["observed_days"], 30)
        self.assertEqual(row["forecast"]["forecast_daily_usage"], D(1))
        self.assertIn("INSUFFICIENT_HISTORY", row["recommendation"]["review_flags"])
        self.assertIsNone(row["recommendation"]["suggested_quantity"])

    def test_no_history_has_no_fabricated_forecast_or_projection(self):
        row = self.one(self.data.items[0], history=())
        self.assertIsNone(row["forecast"]["forecast_daily_usage"])
        self.assertIsNone(row["projection"])
        self.assertEqual(row["recommendation"]["action"], "HUMAN REVIEW")
        self.assertIsNone(row["recommendation"]["lead_time_risk"])
        self.assertIsNone(row["recommendation"]["excess_stock"])

    def test_report_keeps_known_availability_and_marks_unavailable_risk_unknown(self):
        row = self.one(self.data.items[0], history=())
        report = render_report({"as_of": AS_OF, "scenario_names": ["BASELINE"], "recommendations": [row]})
        self.assertIn("| PART-001 | 2 | 110 | unknown | unknown | HUMAN REVIEW | withheld", report)
        self.assertNotIn("none in horizon", report)

    def test_missing_lead_time_and_stale_count_require_review(self):
        row = self.row("KIT-002")
        flags = row["recommendation"]["review_flags"]
        for expected in ("UNKNOWN_LEAD_TIME", "STALE_COUNT", "INCONSISTENT_QUANTITIES", "MISSING_RECEIPT_DATE"):
            self.assertIn(expected, flags)
        self.assertIsNone(row["projection"]["projected_stock_at_lead_time"])
        self.assertIsNone(row["recommendation"]["candidate_quantity"])
        self.assertIsNone(row["recommendation"]["lead_time_risk"])

    def test_negative_inventory_requires_review(self):
        row = self.one(replace(self.data.items[0], current_on_hand=D(-2), allocated_quantity=D(0)))
        self.assertIn("NEGATIVE_INVENTORY", row["recommendation"]["review_flags"])
        self.assertEqual(row["projection"]["stockout_date"], AS_OF)

    def test_spike_and_intermittent_usage_are_not_confident(self):
        self.assertIn("DEMAND_ANOMALY", self.row("PART-007")["recommendation"]["review_flags"])
        self.assertIn("INTERMITTENT_DEMAND", self.row("PART-006")["recommendation"]["review_flags"])
        self.assertEqual(self.row("PART-007")["forecast"]["data_quality"], "low")

    def test_excess_and_zero_recent_demand_are_reviewed_without_disposal(self):
        for item_id in ("PART-008", "KIT-001"):
            self.assertEqual(self.row(item_id)["recommendation"]["action"], "REDUCE / REVIEW EXCESS")
            self.assertTrue(self.row(item_id)["recommendation"]["review_required"])
        self.assertEqual(self.row("KIT-001")["forecast"]["forecast_daily_usage"], D(0))

    def test_scenarios_do_not_mutate_source_records(self):
        original = copy.deepcopy(self.data)
        self.assertEqual(plan(self.data, AS_OF), self.result)
        self.assertEqual(self.data, original)
        for row in self.result["recommendations"]:
            self.assertEqual(row["observed_facts"], self.row(row["item_id"])["observed_facts"])

    def test_demand_increase_changes_projection_and_recommendation(self):
        base, changed = self.row("PART-011"), self.row("PART-011", "DEMAND +20%")
        self.assertEqual(changed["forecast"]["forecast_daily_usage"], D("1.2"))
        self.assertEqual(changed["projection"]["projected_stock_at_lead_time"], D(16))
        self.assertEqual(base["recommendation"]["action"], "MONITOR")
        self.assertEqual(changed["recommendation"]["action"], "ORDER")
        self.assertEqual(changed["recommendation"]["suggested_quantity"], 44)

    def test_lead_time_delay_changes_order_timing_and_quantity(self):
        base, changed = self.row("PART-012"), self.row("PART-012", "LEAD TIME +14 DAYS")
        self.assertEqual(base["recommendation"]["action"], "MONITOR")
        self.assertEqual(changed["recommendation"]["action"], "ORDER")
        self.assertEqual(changed["recommendation"]["lead_time_days"], 49)
        self.assertEqual(changed["recommendation"]["suggested_quantity"], 59)
        self.assertEqual(base["forecast"]["forecast_daily_usage"], changed["forecast"]["forecast_daily_usage"])

    def test_delayed_po_changes_risk_but_does_not_rescue_overdue_po(self):
        delayed = self.row("PART-004", "INBOUND PO DELAYED")
        self.assertEqual(delayed["recommendation"]["action"], "EXPEDITE")
        self.assertEqual(delayed["projection"]["stockout_date"], date(2026, 7, 26))
        self.assertEqual(self.row("PART-005", "INBOUND PO DELAYED")["projection"]["confirmed_inbound_within_horizon"], 0)

    def test_criticality_changes_priority_not_forecast(self):
        item = self.data.items[0]
        low, critical = self.one(replace(item, criticality="low")), self.one(replace(item, criticality="critical"))
        self.assertEqual(low["forecast"], critical["forecast"])
        self.assertEqual(low["projection"], critical["projection"])
        self.assertLess(low["recommendation"]["priority"], critical["recommendation"]["priority"])

    def test_audit_contains_inputs_assumptions_and_explanation(self):
        event = self.result["audit"][0]
        for key in ("item_id", "source_values", "scenario", "forecast", "projected_inventory", "inbound_supply_considered", "recommendation", "policy"):
            self.assertIn(key, event)
        self.assertEqual(event["recommendation"]["human_decision"]["status"], "not_recorded")

    def test_duplicate_po_is_rejected_instead_of_double_counted(self):
        with self.assertRaisesRegex(ValueError, "Duplicate PO reference"):
            check_records(replace(self.data, purchase_orders=self.data.purchase_orders + self.data.purchase_orders[:1]))

    def test_received_cancelled_unconfirmed_orders_are_excluded(self):
        self.assertEqual(self.row()["projection"]["confirmed_inbound_within_horizon"], 0)
        self.assertEqual(self.row("PART-004")["projection"]["confirmed_inbound_within_horizon"], 60)
        self.assertEqual(self.row("PART-008")["projection"]["confirmed_inbound_within_horizon"], 0)

    def test_receipts_after_horizon_are_not_counted_early(self):
        item = self.data.items[0]
        po = PurchaseOrder("PO-SYN-TEST", item.item_id, D(1000), date(2026, 12, 1), "confirmed")
        row = self.one(item, (po,))
        self.assertEqual(row["projection"]["projected_available_at_horizon"], D(20))

    def test_receipt_on_stockout_day_is_available_before_daily_usage(self):
        item = replace(self.data.items[0], current_on_hand=D(10), allocated_quantity=D(0))
        po = PurchaseOrder("PO-SYN-TEST", item.item_id, D(100), date(2026, 7, 11), "confirmed")
        self.assertIsNone(self.one(item, (po,))["projection"]["stockout_date"])

    def test_inbound_recovery_never_creates_zero_quantity_order(self):
        item = replace(self.data.items[0], current_on_hand=D(12), allocated_quantity=D(0))
        po = PurchaseOrder("PO-SYN-TEST", item.item_id, D(100), date(2026, 7, 2), "confirmed")
        self.assertEqual(self.one(item, (po,))["recommendation"]["action"], "MONITOR")

    def test_invalid_numeric_input_and_scenario_are_rejected(self):
        for value in ("NaN", "Infinity"):
            with self.assertRaises(ValueError):
                number(value)
        with self.assertRaises(ValueError):
            Scenario(demand_multiplier=D(-1))

    def test_incomplete_current_month_is_not_treated_as_complete_history(self):
        history = tuple(x for x in self.data.usage if x.item_id == "PART-001")
        value = forecast(history, date(2026, 6, 15))
        self.assertEqual(value["observed_months"], [date(2026, 3, 1), date(2026, 4, 1), date(2026, 5, 1)])
        self.assertEqual(value["baseline_daily_usage"], D(1))

    def test_summary_excludes_withheld_candidates_from_purchase_value(self):
        baseline = [r for r in self.result["recommendations"] if r["scenario"] == "BASELINE"]
        self.assertEqual(summary(baseline)["suggested_purchase_value"], D("2517.00"))

    def test_end_to_end_cli_produces_expected_outputs_and_scenarios(self):
        with tempfile.TemporaryDirectory() as temp:
            completed = subprocess.run([sys.executable, "-m", "operations_forecasting.demo", "--output-dir", temp], capture_output=True, text=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            folder = Path(temp)
            self.assertEqual({p.name for p in folder.iterdir()}, {"recommendations.json", "planning_report.md", "audit.jsonl"})
            output = json.loads((folder / "recommendations.json").read_text(encoding="utf-8"))
            self.assertEqual(len(output["recommendations"]), 56)
            self.assertEqual(len(output["scenario_names"]), 4)
            events = [json.loads(line) for line in (folder / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(events), 56)
            before = {p.name: p.read_bytes() for p in folder.iterdir()}
            write_outputs(self.result, folder)
            self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})


if __name__ == "__main__":
    unittest.main()
