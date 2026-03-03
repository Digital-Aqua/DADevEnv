SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
[ ! -f "$PROJECT_DIR/config.sh" ] || . "$PROJECT_DIR/config.sh"
[ ! -f "$PROJECT_DIR/.env" ] || . "$PROJECT_DIR/.env"


GREEN="\033[32m"
TEAL="\033[36m"
YELLOW="\033[33m"
RED="\033[31m"
NC="\033[0m"

log_h1() {
    echo -e "${GREEN}============== $1 ==============${NC}" >&${LOGSTREAM:-1}
}

log_info() {
    echo -e "${TEAL}$1${NC}" >&${LOGSTREAM:-1}
}

log_warn() {
    echo -e "${YELLOW}WARN: $1${NC}" >&${LOGSTREAM:-1}
}

log_error() {
    echo -e "${RED}ERROR: $1${NC}" >&${LOGSTREAM:-1}   
}

fail() {
    log_error "FATAL: ${1:-Error} (${2:-1})" >&${LOGSTREAM:-1}
    exit "${2:-1}"
}


# Sets the remote server to use for the current session
# when calling `ssh_` or `docker`
REMOTE_SERVER=
export DOCKER_HOST=
set_remote() {
    local KEY=
    local SKIP_CHECK=
    for ARG in "$@"; do
        if [ "$ARG" == "--skip-check" ]; then
            SKIP_CHECK=true
        elif [ -n "$ARG" ]; then
            REMOTE_SERVER="$ARG"
        fi
    done
    if [ -z "$REMOTE_SERVER" ]; then
        log_info "Working locally."
        REMOTE_SERVER=
        export DOCKER_HOST=
        return
    fi
    export DOCKER_HOST="ssh://${REMOTE_USERS[$REMOTE_SERVER]}@${REMOTE_SERVERS[$REMOTE_SERVER]}"
    if [ -n "$SKIP_CHECK" ]; then
        TOKEN="$RANDOM"
        ssh_ "echo $TOKEN" \
            | grep -q "^$TOKEN$" \
            || fail "Failed to connect to remote server"
    fi
    log_info "Working on remote '$REMOTE_SERVER' ($DOCKER_HOST)."
}

# Runs a command on the server set by `set_remote` using `ssh`.
# Runs the command in a subshell if the server is localhost.
ssh_() {
    local HOSTNAME="${REMOTE_SERVERS[$REMOTE_SERVER]}"
    local COMMAND=""
    for ARG in "$@"; do
        COMMAND="$COMMAND $(printf '%q' "$ARG")"
    done
    COMMAND="$SHELL -c '$COMMAND'"
    if [ -z "$HOSTNAME" ] \
        || [ "$HOSTNAME" == "localhost" ] \
        || [ "$HOSTNAME" == "127.0.0.1" ]
    then
        eval $COMMAND
        return
    fi
    local USER="${REMOTE_USERS[$REMOTE_SERVER]}"
    ssh "$USER@$HOSTNAME" "$COMMAND"
}

# Waits for a container to become healthy.
# Usage: docker_wait_for_healthy <container> [timeout=60]
docker_wait_for_healthy() {
    local CONTAINER="$1"
    local TIMEOUT="${2:-60}"  # Default 60 seconds
    log_info "Waiting for '$CONTAINER' to become healthy..."
    
    if timeout "$TIMEOUT" bash -c "until docker inspect --format='{{.State.Health.Status}}' '$CONTAINER' 2>/dev/null | grep -q '^healthy$'; do sleep 1; done"; then
        log_info "$CONTAINER is healthy."
        return 0
    else
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null)
        log_error "Timeout waiting for '$CONTAINER' to become healthy. Status: ${health_status:-unknown}"
        docker logs "$CONTAINER" 2>&1 | tail -20
        return 1
    fi
}

# Extracts container names from docker compose output.
# Usage: grep_array <input> <extract_regex> [output_var]
#   extract_regex: Perl regex with \K; matched part becomes array elements.
#   e.g. 'container \K.+(?= is unhealthy| exited \(\d+\))'
grep_array() {
    local input="$1"
    local rx="$2"
    local out_var="${3:-REPLY}"
    local -n out="$out_var"
    out=()
    while IFS= read -r name; do
        [[ -n "$name" ]] && out+=("$name")
    done < <(echo "$input" | grep -oP "$rx" 2>/dev/null | sort -u || true)
}

# Wrapper for docker compose.
# If no arguments are provided, it pulls, builds, ups, detaches, waits for
# healthy status, and removes orphans.
# Usage: docker_compose_wrapper <working-dir> <compose-file> [args...]
docker_compose_wrapper() {
    local WORKING_DIR="$1"
    local COMPOSE_FILE="$2"
    local WAIT_TIMEOUT="${DOCKER_COMPOSE_WAIT_TIMEOUT:-30}"
    shift; shift
    local ARGS=("$@")
    if [ ${#ARGS[@]} -gt 0 ] && [ "${ARGS[0]}" = "inspect" ]; then
        local INSPECT_ARGS=("${ARGS[@]:1}")
        local INSPECT_TARGETS=()
        local PS_OUTPUT
        # Inspect all project containers.
        PS_OUTPUT="$(docker compose \
            --project-directory "$WORKING_DIR" \
            --file "$COMPOSE_FILE" \
            ps -q)" || return $?
        mapfile -t INSPECT_TARGETS <<< "$PS_OUTPUT"

        if [ ${#INSPECT_TARGETS[@]} -eq 0 ]; then
            log_warn "No containers found to inspect for $WORKING_DIR."
            return 0
        fi
        docker inspect "${INSPECT_ARGS[@]}" "${INSPECT_TARGETS[@]}"
        return $?
    fi
    if [ ${#ARGS[@]} -eq 0 ]; then
        ARGS=(up --pull always --build --detach --wait --remove-orphans --wait-timeout "$WAIT_TIMEOUT")
    fi
    local TMP OUTPUT EXIT_CODE
    TMP="$(mktemp)"
    trap "rm -f '$TMP'" EXIT
    docker compose \
        --project-directory "$WORKING_DIR" \
        --file "$COMPOSE_FILE" \
        "${ARGS[@]}" 2> >(tee "$TMP" >&2) || EXIT_CODE=$?
    EXIT_CODE=${EXIT_CODE:-$?}
    OUTPUT="$(cat "$TMP")"
    if [ $EXIT_CODE -ne 0 ]; then
        log_error "Docker Compose exited with code $EXIT_CODE."
        echo "$OUTPUT" >&2
        local CONTAINERS
        grep_array "$OUTPUT" 'container \K.+(?= is unhealthy| exited \(\d+\))' CONTAINERS
        if [ ${#CONTAINERS[@]} -gt 0 ]; then
            log_error "Problem container(s) detected (unhealthy or exited)."
            for container in "${CONTAINERS[@]}"; do
                log_info "Logs for $container:"
                docker logs "$container" --since 2m 2>&1 || true
            done
            exit $EXIT_CODE
        fi
        exit $EXIT_CODE
    fi
    log_info "Docker Compose exited successfully."
}
