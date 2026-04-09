#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

answer = Path('answer.txt')
if not answer.exists():
    raise SystemExit('answer.txt not found')
if answer.read_text(encoding='utf-8').strip() != 'src/region.py':
    raise SystemExit('unexpected answer')
print('PASS')
PY
