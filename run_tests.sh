#!/usr/bin/env bash

set -euo pipefail

if [ $# -ge 1 ]; then
    dir="$1"
else
    dir=test/solution_tests/
fi

PYTHONPATH=lib python -m pytest -q "$dir"
