# Changelog

## Unreleased
- Several imgchest accounts, one key each (`IMG_CHEST_API_KEY_<NAME>`). A refused key fails over
  to the next account. `--account` or `imgchest_accounts` picks which to use. Links record
  their account.
- Accounts that run out of storage are flagged in the database (`imgchest_accounts`, shared with
  imguploader) and skipped on later runs.
- imgchest's hourly limit (HTTP 429) stops uploads for the run.
- `--upload` works with configs that have no database keys.
- Schema upgrades lock `image_cache` only when a column is actually missing, so pixBoards can run
  while imguploader uploads.

## 1.0.1

- Big internal refactor: nothing runs at import time, and `pixboards` / `python -m pixBoards`
  return proper exit codes.
- Justified layout rewritten:
  - rows fill the width edge to edge;
  - nothing is cropped;
  - the last row isn't stretched;
  - image sizes are known before the images load.
- Board pages:
  - sticky toolbar;
  - lightbox: click an image to open it; Shift+click copies its link;
  - keyboard shortcuts: ←/→ change page, R opens a random page, J switches the layout;
  - row-height slider, back-to-top button and a working jump-to-page box;
  - a "Random Page" button above the grid.
- Index: thumbnails, collapsible folders, a search box.
- Optional "open on Pinterest" links for gallery-dl downloads (`pinterest_<pinId>` file names):
  - a toolbar toggle, a hover badge, a lightbox link and the P key;
  - off by default; `source_links: true` turns it on.
- Much faster re-runs: hashes, image sizes and dates are cached in `~/.cache/pixboards`, so only
  new or changed files are read. A warm run over about 5,000 images takes about 0.3 s.
- Uploads:
  - links always line up with their files;
  - each upload is saved immediately;
  - database errors roll back;
  - requests time out;
  - files are sent with their real MIME types.
- Flags:
  - `--recent N` keeps the newest N images (EXIF date, else file time);
  - `--reddit` sorts by reddit post id;
  - `--gitPush` works and never exposes the token.
- New config keys: `default_layout`, `row_height` (was `height`), `lazy_loading`, `source_links`,
  `json_dump`, `cache_file`. `~` and `$VARS` work in paths.
- Packaging:
  - `pyproject.toml`; Python 3.10 or newer is required;
  - database and upload dependencies are optional (`pip install "pixboards[upload]"`);
  - pytest suite and GitHub Actions CI.
- The repo is Linux-first: `scripts/publish.sh` and `scripts/release.sh` replace the Windows batch
  files, and `gui.py` and `main.py` are gone.
- More detail in [docs/1.0.1-report.md](docs/1.0.1-report.md).

## 0.2.33
- Recent boards sort by image metadata properly.
- Layout and column settings work on local HTML files too; they are saved in both a cookie and
  localStorage.

## 0.2.31
- Several bug fixes.
- The input folder is no longer cluttered with JSON dumps.

## 0.2.30
- Fixed `default_layout` not working.

## 0.2.29
- Row height for the justified layout can be set.

## 0.2.26
- The page background is a random image from the page.
- The title and heading use the board name, and there is a favicon (in the templates folder).
- Works without a running PostgreSQL server.
- The repository moved to https://github.com/flynnsharwood/pixBoards.
