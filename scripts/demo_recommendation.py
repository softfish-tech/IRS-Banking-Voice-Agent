"""Run a deterministic D-only synthetic demonstration, not the full agent."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.dont_write_bytecode = True

from banking_agent.modules.recommendation import load_fixture, recommend


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["S05", "S06", "S09", "S10"], default="S06")
    parser.add_argument(
        "--fixture", type=Path, default=root / "data/fixtures/recommendation.json"
    )
    args = parser.parse_args()
    fixture = load_fixture(args.fixture)
    cases = json.loads(
        (root / "tests/fixtures/scenarios/recommendation.json").read_text(encoding="utf-8")
    )
    case = next(case for case in cases["scenarios"] if case["id"] == args.scenario)
    result = recommend(
        case["request"],
        customer_profiles=fixture.customer_profiles,
        products=fixture.products,
    )
    expected = case["expected_d"]
    if result["status"] != "ok" or {
        "allowed": result["data"]["allowed"],
        "reason_code": result["data"]["reason_code"],
        "product_ids": [item["product_id"] for item in result["data"]["items"]],
    } != expected:
        raise SystemExit("D demo result does not match scenario expectations")
    print(json.dumps({
        "scenario": args.scenario,
        "synthetic": True,
        "direct_module_demo": True,
        "expected_integrated_d_called": case["expected_d_called"],
        "result": result,
    }, indent=2))


if __name__ == "__main__":
    main()
