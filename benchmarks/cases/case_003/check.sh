#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export SCRIPT_DIR

EXPECTED="$SCRIPT_DIR/expected/src/stats.py"
ACTUAL="src/stats.py"

cmp -s "$EXPECTED" "$ACTUAL"

script_dir="$SCRIPT_DIR"
root="$(pwd)"
fixture_root="$script_dir/workspace"
allowed_extra="autodarwin-case.json autodarwin-prompt.txt"

for fixture_file in $(cd "$fixture_root" && find . -type f | sort); do
    rel="${fixture_file#./}"
    case "$rel" in
        __pycache__/*|.pytest_cache/*|.DS_Store) continue ;;
    esac
    case "$rel" in
        src/stats.py|autodarwin-case.json|autodarwin-prompt.txt) continue ;;
    esac
    if [ ! -f "$rel" ]; then
        echo "missing file: $rel" >&2
        exit 1
    fi
    cmp -s "$fixture_root/$rel" "$rel"
done

for actual_file in $(find . -type f | sort); do
    rel="${actual_file#./}"
    case "$rel" in
        __pycache__/*|.pytest_cache/*|.DS_Store) continue ;;
    esac
    case "$rel" in
        src/stats.py|autodarwin-case.json|autodarwin-prompt.txt) continue ;;
    esac
    if [ ! -f "$fixture_root/$rel" ]; then
        echo "unexpected extra file: $rel" >&2
        exit 1
    fi
done

echo PASS
