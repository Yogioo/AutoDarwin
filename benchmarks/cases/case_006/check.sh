#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export SCRIPT_DIR

python3 - <<'PY'
from pathlib import Path
import os

script_dir = Path(os.environ["SCRIPT_DIR"])
root = Path.cwd()
expected = (script_dir / "expected" / "README.md").read_text(encoding="utf-8")
actual_path = root / "README.md"
if not actual_path.exists():
    raise SystemExit("README.md not found")
actual = actual_path.read_text(encoding="utf-8")
if actual != expected:
    raise SystemExit("README.md does not match expected content")

allowed_extra = {Path("autodarwin-case.json"), Path("autodarwin-prompt.txt")}
for path in root.rglob("*"):
    if path.is_file() and path.relative_to(root) != Path("README.md") and path.relative_to(root) not in allowed_extra:
        raise SystemExit(f"unexpected extra file: {path.relative_to(root)}")

print("PASS")
PY
