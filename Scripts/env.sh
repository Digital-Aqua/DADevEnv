#!/bin/bash

# Installs, updates, and activates a development environment.
# 
# Usage:
#   `./env.sh` - Install/update environment
#   `./env.sh <command>` - Run command in environment
#   `. ./env.sh` or `source ./env.sh` - Activate environment in current shell
# 
# Installation:
#   1. Clone gist into External/env.sh (or similar)
#   2. Symlink via `ln -s ./External/env.sh/env.sh` (or similar)
#   3. Add contents of `settings.json` to `.vscode/settings.json`
#   4. Create an `environment.yaml` file
#   5. Run `./env.sh` to install the environment

set -euo pipefail
ENVSH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVSH_PREFIX="${ENVSH_DIR}/.micromamba"

ENVSH_WATCHES=(
    "environment.yaml"
    "pyproject.toml"
    #"pnpm-workspace.yaml" -- TODO (pnpm has a complex installation process)
)

function info() {
    echo -e "\033[38;5;39m[env.sh]\033[0m $1" >&2
}

function error() {
    echo -e "\033[31m[env.sh] [ERROR] $1\033[0m" >&2
}

function ensure_micromamba() {
    if ! command -v micromamba &> /dev/null; then
        info "Micromamba not found."
        if ! command -v curl &> /dev/null; then
            error "Curl not found. Please install it manually so micromamba can be downloaded."
            exit 1
        fi
    fi
}

function _mm() {
    micromamba -p "${ENVSH_PREFIX}" "$@"
}

function ensure_prefix() {
    if [ ! -d "${ENVSH_PREFIX}" ]; then
        info "Creating prefix..."
        _mm create
    fi
}

function check_watch() {
    local WATCH="$1"
    [ -f "${ENVSH_DIR}/${WATCH}" ] || return 0
    [ -f "${ENVSH_PREFIX}/.watch/${WATCH}" ] || return 1
    cmp -s "${ENVSH_DIR}/${WATCH}" "${ENVSH_PREFIX}/.watch/${WATCH}" || return 1
}

function check_watches() {
    mkdir -p "${ENVSH_PREFIX}/.watch"
    for WATCH in "${ENVSH_WATCHES[@]}"; do
        check_watch "${WATCH}" || return 1
    done
    info "Prefix is up-to-date."
}

function copy_watches() {
    rm -rf "${ENVSH_PREFIX}/.watch"
    mkdir -p "${ENVSH_PREFIX}/.watch"
    for WATCH in "${ENVSH_WATCHES[@]}"; do
        [ ! -f "${ENVSH_DIR}/${WATCH}" ] || \
            cp "${ENVSH_DIR}/${WATCH}" "${ENVSH_PREFIX}/.watch/${WATCH}"
    done
}

function _envsh_set_prompt() {
    case "$-" in
        *i*) : ;;
        *) return ;;
    esac

    local project_name="${ENVSH_PROMPT_PROJECT:-$(basename "${ENVSH_DIR}")}"
    local reset='\[\e[0m\]'
    local c_project='\[\e[38;5;39m\]'   # blue-ish
    local c_path='\[\e[38;5;250m\]'     # light gray
    export PS1="${c_project}(${project_name})${reset} ${c_path}\\w${reset}\\$ "
}

function main() {
    # Load micromamba into shell
    ensure_micromamba
    set +u; eval "$(micromamba shell hook --shell bash)"; set -u

    # Check the prefix is up-to-date
    ensure_prefix
    if ! check_watches; then
        info "Updating prefix..."
        _mm env update -y -f "${ENVSH_DIR}/environment.yaml"
        copy_watches
        info "Update complete."
    fi

    # If we have args, run them via micromamba
    if [ ${#@} -gt 0 ]; then
        info "Running command via micromamba..."
        _mm run "$@" || exit $?
        exit 0
    
    # If we are being sourced, activate the environment
    elif [ "${BASH_SOURCE[0]}" != "${0}" ]; then
        info "Activating environment..."
        set +u; micromamba activate -p "${ENVSH_PREFIX}"; set -u
        _envsh_set_prompt
        set +e
    
    # Otherwise, do nothing more
    fi
}

main "$@"
