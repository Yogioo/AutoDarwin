#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export SCRIPT_DIR

python3 - <<'PY'
from pathlib import Path
import os

script_dir = Path(os.environ["SCRIPT_DIR"])
root = Path.cwd()
expected_answer = "app/notes.py"

answer_path = root / "answer.txt"
if not answer_path.exists():
    raise SystemExit("answer.txt not found")
answer = answer_path.read_text(encoding="utf-8").strip()
if answer != expected_answer:
    raise SystemExit(f"unexpected answer: {answer!r} != {expected_answer!r}")

fixture_root = script_dir / "workspace"
ignore_names = {"__pycache__", ".pytest_cache", ".DS_Store"}

for fixture_file in fixture_root.rglob("*"):
    if not fixture_file.is_file():
        continue
    rel = fixture_file.relative_to(fixture_root)
    if any(part in ignore_names for part in rel.parts):
        continue
    actual = root / rel
    if not actual.exists():
        raise SystemExit(f"missing file: {rel}")
    if actual.read_text(encoding="utf-8") != fixture_file.read_text(encoding="utf-8"):
        raise SystemExit(f"fixture file changed unexpectedly: {rel}")

allowed_extra = {Path("answer.txt"), Path("autodarwin-case.json"), Path("autodarwin-prompt.txt")}
for actual_file in root.rglob("*"):
    if not actual_file.is_file():
        continue
    rel = actual_file.relative_to(root)
    if any(part in ignore_names for part in rel.parts):
        continue
    if rel in allowed_extra:
        continue
    if not (fixture_root / rel).exists():
        raise SystemExit(f"unexpected extra file: {rel}")

print("PASS")
PY
