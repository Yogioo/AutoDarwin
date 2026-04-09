#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cmp -s "$SCRIPT_DIR/expected/src/slug.py" src/slug.py

echo PASS
