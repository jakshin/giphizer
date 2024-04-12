#!/usr/bin/env bash
set -e
script_dir="$(dirname -- "$(readlink -- "${BASH_SOURCE[0]}" || echo "${BASH_SOURCE[0]}")")"
cd -- "$script_dir"

# Pass through options, such as -v, -p to override the default here, etc.
python3 -m unittest discover -p '*_test.py' "$@"
