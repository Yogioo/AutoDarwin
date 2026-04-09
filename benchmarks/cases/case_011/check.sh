#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cmp -s "$SCRIPT_DIR/expected/config.json" config.json
cmp -s "$SCRIPT_DIR/workspace/config.example.json" config.example.json

echo PASS
