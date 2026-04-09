#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXPECTED="$SCRIPT_DIR/expected/package/runner.py"
FIXTURE_ROOT="$SCRIPT_DIR/workspace"

cmp -s "$EXPECTED" "package/runner.py"

for fixture_file in $(cd "$FIXTURE_ROOT" && find . -type f | sort); do
    rel="${fixture_file#./}"
    case "$rel" in
        __pycache__/*|.pytest_cache/*|.DS_Store) continue ;;
    esac
    case "$rel" in
        package/runner.py|autodarwin-case.json|autodarwin-prompt.txt) continue ;;
    esac
    if [ ! -f "$rel" ]; then
        echo "missing file: $rel" >&2
        exit 1
    fi
    cmp -s "$FIXTURE_ROOT/$rel" "$rel"
done

for actual_file in $(find . -type f | sort); do
    rel="${actual_file#./}"
    case "$rel" in
        __pycache__/*|.pytest_cache/*|.DS_Store) continue ;;
    esac
    case "$rel" in
        package/runner.py|autodarwin-case.json|autodarwin-prompt.txt) continue ;;
    esac
    if [ ! -f "$FIXTURE_ROOT/$rel" ]; then
        echo "unexpected extra file: $rel" >&2
        exit 1
    fi
done

echo PASS
