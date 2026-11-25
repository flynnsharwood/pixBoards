#!/usr/bin/env bash
# Build pixBoards and upload the current version to PyPI, then tag it.
#   scripts/release.sh        build, check, ask, upload, tag
#   scripts/release.sh -n     build and check only
# Needs: python -m build, twine (pip install build twine)
set -euo pipefail

REPO_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON=${PYTHON:-python3}
cd "$REPO_DIR"

die() { echo "error: $*" >&2; exit 1; }

BUILD_ONLY=0
[[ ${1:-} == -n ]] && BUILD_ONLY=1

VERSION=$("$PYTHON" -c 'import re; print(re.search(r"__version__\s*=\s*\"([^\"]+)\"", open("pixBoards/__init__.py").read()).group(1))')
TAG="v$VERSION"
echo "==> pixboards $VERSION"

"$PYTHON" -m build --version >/dev/null 2>&1 || die "missing 'build' (pip install build)"
"$PYTHON" -m twine --version >/dev/null 2>&1 || die "missing 'twine' (pip install twine)"

if [[ -n $(git status --porcelain --untracked-files=no) ]]; then
    echo "warning: uncommitted changes; the build will include them" >&2
fi
if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
    die "tag $TAG already exists; bump __version__ in pixBoards/__init__.py"
fi

rm -rf build "dist/pixboards-$VERSION"* ./*.egg-info
"$PYTHON" -m build
"$PYTHON" -m twine check "dist/pixboards-$VERSION"*

[[ $BUILD_ONLY == 1 ]] && { echo "==> built dist/pixboards-$VERSION*"; exit 0; }

read -r -p "Upload pixboards $VERSION to PyPI? [y/N] " answer
[[ $answer == [yY] ]] || die "aborted"

"$PYTHON" -m twine upload "dist/pixboards-$VERSION"*
git tag -a "$TAG" -m "pixboards $VERSION"
echo "==> uploaded and tagged $TAG; push the tag with: git push origin $TAG"
