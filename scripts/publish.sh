#!/usr/bin/env bash
# Build pixBoards profiles and publish their upload build to GitHub Pages.
# Linux replacement for the old Windows batch files (everything*.bat).
#
# Profiles live in scripts/publish.conf (git-ignored); start from
# scripts/publish.conf.example.
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_DIR=$(dirname -- "$SCRIPT_DIR")
CONF=${PUBLISH_CONF:-$SCRIPT_DIR/publish.conf}
PYTHON=${PYTHON:-python3}

UPLOAD=0 DOWNLOAD=0 OPEN=0 DRY_RUN=0

usage() {
    cat <<EOF
Usage: $(basename "$0") [options] PROFILE... | all

Builds each profile's local boards. With -u it also builds the --upload
version and pushes it to the profile's GitHub Pages repo.

Options:
  -u   build the upload version and push it to REMOTE
  -d   run the profile's download step first (if it defines one)
  -o   open the local index.html when done
  -n   dry run: print the commands without running them
  -l   list the profiles in the config
  -c   config file (default: $CONF)
  -h   show this help

Examples:
  $(basename "$0") -u pinterest
  $(basename "$0") -u -d all
EOF
}

die() { echo "error: $*" >&2; exit 1; }
log() { echo "==> $*" >&2; }
run() {
    printf '+' >&2; printf ' %q' "$@" >&2; echo >&2
    [[ $DRY_RUN == 1 ]] || "$@"
}

# Ask pixBoards itself where a run writes its output, so this script never
# duplicates the masterDir/outputDir rules from config_loader.py.
output_dir() {
    (cd "$REPO_DIR" && "$PYTHON" - "$@" <<'PY'
import sys
from pixBoards.arguments import parse_args
from pixBoards.config_loader import ConfigError, build_config
try:
    print(build_config(parse_args(sys.argv[1:]))["outputDir"])
except ConfigError as e:
    sys.exit(f"error: {e}")
PY
    )
}

check_output_dir() {
    local dir=$1
    if [[ $dir =~ ^[A-Za-z]:[\\/] ]]; then
        die "profile '$PROFILE': output folder '$dir' is a Windows path." \
            "Update masterDir in ${CONFIG:-config.yml}."
    fi
}

pixboards() {
    (cd "$REPO_DIR" && run "$PYTHON" -m pixBoards "$@")
}

deployments_url() {
    # git@github.com:owner/repo.git or https://[user@]github.com/owner/repo(.git)
    local re='^(git@github\.com:|https://([^@/]+@)?github\.com/)([^/]+/[^/]+)$'
    [[ $1 =~ $re ]] || return 1
    echo "https://github.com/${BASH_REMATCH[3]%.git}/deployments"
}

publish_dir() {
    local dir=$1
    [[ -n ${REMOTE:-} ]] || die "profile '$PROFILE' has no REMOTE set"
    [[ -d $dir || $DRY_RUN == 1 ]] || die "output folder '$dir' doesn't exist"

    [[ -d $dir/.git ]] || run git -C "$dir" init -q -b main
    [[ -n ${GIT_NAME:-} ]] && run git -C "$dir" config user.name "$GIT_NAME"
    [[ -n ${GIT_EMAIL:-} ]] && run git -C "$dir" config user.email "$GIT_EMAIL"

    if git -C "$dir" remote get-url origin >/dev/null 2>&1; then
        run git -C "$dir" remote set-url origin "$REMOTE"
    else
        run git -C "$dir" remote add origin "$REMOTE"
    fi

    run git -C "$dir" add -A
    if [[ -d $dir/.git ]] && git -C "$dir" diff --cached --quiet; then
        log "$PROFILE: nothing new to commit"
    else
        run git -C "$dir" commit -q -m "pixBoards publish $(date '+%Y-%m-%d %H:%M')"
    fi

    local push_flags=(-u)
    [[ ${FORCE_PUSH:-0} == 1 ]] && push_flags+=(--force)
    run git -C "$dir" push "${push_flags[@]}" origin HEAD:main

    local url
    if url=$(deployments_url "$REMOTE"); then
        log "$PROFILE: deployments at $url"
    fi
}

run_profile() {
    PROFILE=$1
    declare -F "profile_$PROFILE" >/dev/null || die "unknown profile '$PROFILE' (see -l)"

    # reset settings so nothing leaks from the previous profile
    CONFIG="" REMOTE="" GIT_NAME="" GIT_EMAIL="" FORCE_PUSH=0
    BUILD_ARGS=() UPLOAD_ARGS=()
    "profile_$PROFILE"

    local cfg=()
    [[ -n $CONFIG ]] && cfg=(--config "$CONFIG")

    if [[ $DOWNLOAD == 1 ]] && declare -F "download_$PROFILE" >/dev/null; then
        log "$PROFILE: downloading"
        if [[ $DRY_RUN == 1 ]]; then echo "+ download_$PROFILE" >&2; else "download_$PROFILE"; fi
    fi

    local local_dir
    local_dir=$(output_dir "${cfg[@]}")
    check_output_dir "$local_dir"
    log "$PROFILE: building $local_dir"
    pixboards "${cfg[@]}" "${BUILD_ARGS[@]}"

    if [[ $UPLOAD == 1 ]]; then
        local upload_dir
        upload_dir=$(output_dir "${cfg[@]}" --upload)
        check_output_dir "$upload_dir"
        log "$PROFILE: building upload version $upload_dir"
        pixboards "${cfg[@]}" --upload "${BUILD_ARGS[@]}" "${UPLOAD_ARGS[@]}"
        publish_dir "$upload_dir"
    fi

    if [[ $OPEN == 1 && $DRY_RUN == 0 ]]; then
        xdg-open "$local_dir/index.html" >/dev/null 2>&1 &
    fi
}

main() {
    local list=0 opt
    while getopts ":udonlc:h" opt; do
        case $opt in
            u) UPLOAD=1 ;;
            d) DOWNLOAD=1 ;;
            o) OPEN=1 ;;
            n) DRY_RUN=1 ;;
            l) list=1 ;;
            c) CONF=$OPTARG ;;
            h) usage; exit 0 ;;
            :) die "-$OPTARG needs a value" ;;
            *) usage >&2; exit 2 ;;
        esac
    done
    shift $((OPTIND - 1))

    [[ -f $CONF ]] || die "no config at $CONF (copy scripts/publish.conf.example)"
    PROFILES=()
    # shellcheck source=publish.conf.example
    source "$CONF"

    if [[ $list == 1 ]]; then
        printf '%s\n' "${PROFILES[@]}"
        exit 0
    fi
    [[ $# -gt 0 ]] || { usage >&2; exit 2; }

    local targets=("$@")
    [[ $1 == all ]] && targets=("${PROFILES[@]}")
    for p in "${targets[@]}"; do
        run_profile "$p"
    done
}

main "$@"
