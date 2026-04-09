#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export SCRIPT_DIR

rm -rf output data/output
python3 tools/export_report.py data/sample.json output/report.txt

python3 - <<'PY'
from pathlib import Path

root = Path.cwd()
expected_lines = "title=weekly\ncount=3\n"

report = root / "output" / "report.txt"
if not report.exists():
    raise SystemExit("output/report.txt not found")
if report.read_text(encoding="utf-8") != expected_lines:
    raise SystemExit("report content mismatch")

wrong = root / "data" / "output" / "report.txt"
if wrong.exists():
    raise SystemExit("wrong output path produced: data/output/report.txt")

print("PASS")
PY

cmp -s "$SCRIPT_DIR/expected/tools/export_report.py" tools/export_report.py
