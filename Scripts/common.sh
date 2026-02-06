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
    echo -e "${GREEN}============== $1 ==============${NC}"
}

log_info() {
    echo -e "${TEAL}$1${NC}"
}

log_warn() {
    echo -e "${YELLOW}WARN: $1${NC}"
}

log_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

fail() {
    log_error "FATAL: ${1:-Error} (${2:-1})"
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
