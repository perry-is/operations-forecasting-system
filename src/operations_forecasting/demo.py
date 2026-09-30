"""Offline scenario using exclusively fictional records."""

import argparse
from datetime import date
from decimal import Decimal
from pathlib import Path

from .ingest import load_data
from .reporting import summary, write_outputs
from .workflow import plan

ROOT = Path(__file__).resolve().parents[2]
AS_OF = date(2026, 6, 30)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "generated_example")
    parser.add_argument("--horizon-days", type=int, default=90)
    parser.add_argument("--safety-factor", type=Decimal, default=Decimal("1.25"))
    args = parser.parse_args()
    result = plan(load_data(ROOT / "examples"), AS_OF,
                  horizon_days=args.horizon_days, safety_factor=args.safety_factor)
    write_outputs(result, args.output_dir)
    baseline = [r for r in result["recommendations"] if r["scenario"] == "BASELINE"]
    print("Synthetic planning complete: 4 scenarios; no purchasing actions executed.")
    for key, value in summary(baseline).items():
        print(f"{key}: {value}")
    print("Outputs: recommendations.json, planning_report.md, audit.jsonl")


if __name__ == "__main__":
    main()
