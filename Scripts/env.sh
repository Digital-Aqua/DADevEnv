#!/bin/bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PREFIX="${DIR}/.conda"

. "$DIR/Scripts/common.sh"

function ensure_micromamba() {
    if ! command -v micromamba &> /dev/null; then
        echo "Micromamba not found." >&2
        if ! command -v curl &> /dev/null; then
            echo "Curl not found. Please install it manually so micromamba can be downloaded." >&2
            exit 1
        fi
    fi
}

function _mm() {
    micromamba -p "${PREFIX}" "$@"
}

function ensure_prefix() {
    if [ ! -d "${PREFIX}" ]; then
        echo "Creating prefix..." >&2
        _mm create
        
        local SCRIPT_ENV_VARS="${PREFIX}/etc/conda/activate.d/dadevenv.sh"
        mkdir -p "$(dirname "${SCRIPT_ENV_VARS}")"
        {
            echo "#!/bin/bash" > "${SCRIPT_ENV_VARS}"
            echo "export PATH=\"${SCRIPTS}:\${PATH}\""
        } > "${SCRIPT_ENV_VARS}"
        chmod +x "${SCRIPT_ENV_VARS}"
    fi
}

WATCHES=(
    "environment.yaml"
    "pyproject.toml"
)

function check_watch() {
    local WATCH="$1"
    [ -f "${DIR}/${WATCH}" ] || return 0
    [ -f "${PREFIX}/.watch/${WATCH}" ] || return 1
    cmp -s "${DIR}/${WATCH}" "${PREFIX}/.watch/${WATCH}" || return 1
}

function check_watches() {
    mkdir -p "${PREFIX}/.watch"
    for WATCH in "${WATCHES[@]}"; do
        check_watch "${WATCH}" || return 1
    done
    echo "Prefix is up-to-date." >&2
}

function copy_watches() {
    rm -rf "${PREFIX}/.watch"
    mkdir -p "${PREFIX}/.watch"
    for WATCH in "${WATCHES[@]}"; do
        [ ! -f "${DIR}/${WATCH}" ] || \
            cp "${DIR}/${WATCH}" "${PREFIX}/.watch/${WATCH}"
    done
}

function main() {
    # Load micromamba into shell
    ensure_micromamba
    eval "$(micromamba shell hook --shell bash)"

    # Check the prefix is up-to-date
    ensure_prefix
    if ! check_watches; then
        echo "Updating prefix..." >&2
        _mm env update -y -f "${DIR}/environment.yaml"
        copy_watches
        echo "Update complete." >&2
    fi

    # If we have args, run them via micromamba
    if [ ${#@} -gt 0 ]; then
        echo "Running command via micromamba..." >&2
        micromamba run -p "${PREFIX}" "$@"
        exit $?
    # If we are being sourced, activate the environment
    elif [ "${BASH_SOURCE[0]}" != "${0}" ]; then
        set +u
        echo "Activating environment..." >&2
        micromamba activate -p "${PREFIX}"
        set -u
    fi
    # Otherwise, do nothing more
}

main "$@"
