#!/bin/bash
# Runs the scripts in the `{script_basename}.d/` directory.
set -o pipefail

SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_NAME="$(basename "$SCRIPT_PATH")"
BASE_NAME="${SCRIPT_NAME%.sh}"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
RUN_D_DIR="$SCRIPT_DIR/${BASE_NAME}.d"
HAS_FAILURE=0

if [[ -d "$RUN_D_DIR" ]]; then
  shopt -s nullglob
  for script_file in "$RUN_D_DIR"/*.sh; do
    if ! bash "$script_file"; then
      HAS_FAILURE=1
    fi
  done
  shopt -u nullglob
fi

if (( HAS_FAILURE != 0 )); then
  exit 1
fi
