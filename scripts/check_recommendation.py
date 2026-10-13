"""Validate available repository test layers; optionally require E/real-D checks."""
import argparse
from pathlib import Path
import subprocess
import sys
import unittest

if sys.version_info < (3, 11):
    raise SystemExit("This project requires Python 3.11 or newer.")

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
sys.dont_write_bytecode = True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e-integration", action="store_true",
                        help="Require E files and run the real-D orchestrator checks.")
    args = parser.parse_args()
    if args.e_integration and not (ROOT / "src/banking_agent/app/orchestrator/orchestrator.py").is_file():
        raise SystemExit("E integration is absent; this option cannot be verified on main alone.")
    suite = unittest.TestSuite()
    layers = ["unit", "integration"]
    if any((ROOT / "tests/e2e").glob("test_*.py")):
        layers.append("e2e")
    for layer in layers:
        tests = unittest.TestLoader().discover(
            str(ROOT / "tests" / layer), pattern="test_*.py"
        )
        count = tests.countTestCases()
        if count == 0:
            raise SystemExit(f"No tests discovered in {layer}; validation is incomplete.")
        print(f"{layer}: {count} tests", flush=True)
        suite.addTests(tests)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    if not outcome.wasSuccessful() or outcome.skipped:
        raise SystemExit("Tests failed or were skipped.")
    sources = [*ROOT.glob("src/**/*.py"), *ROOT.glob("tests/**/*.py"), *ROOT.glob("scripts/*.py")]
    for path in sources:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    print(f"Compiled {len(sources)} Python source files without writing caches.")
    if args.e_integration:
        subprocess.run([sys.executable, "-B", str(ROOT / "scripts/check_recommendation_e.py")],
                       cwd=ROOT, check=True)
    elif "e2e" not in layers:
        print("E is absent: no full-system E2E completion is claimed.")


if __name__ == "__main__":
    main()
