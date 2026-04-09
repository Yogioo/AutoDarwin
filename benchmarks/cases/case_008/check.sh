#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export SCRIPT_DIR

bash verify.sh

EXPECTED="src/formatter.py"
cmp -s "$SCRIPT_DIR/expected/$EXPECTED" "$EXPECTED"

for rel in $(find . -type f | sort); do
    rel="${rel#./}"
    case "$rel" in
        __pycache__/*|.pytest_cache/*|.DS_Store) continue ;;
    esac
    case "$rel" in
        src/formatter.py|autodarwin-case.json|autodarwin-prompt.txt) continue ;;
    esac
    if [ ! -f "$SCRIPT_DIR/workspace/$rel" ]; then
        echo "unexpected extra file: $rel" >&2
        exit 1
    fi
    cmp -s "$SCRIPT_DIR/workspace/$rel" "$rel"
done

echo PASS
