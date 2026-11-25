# notice

repo finally changed to [https://github.com/flynnsharwood/pixBoards.git](https://github.com/flynnsharwood/pixBoards.git)

title and heading use the board name now. favicon added, can be changed, check the templates folder. 

the bg image is now a random image from the page. (pixboards 0.2.26)

you can specify height for justified layout now (pixboards 0.2.29)

~~if you are using the PyPi package, you will need to have a running postgres server, else it won't work.~~ It works now. 

fixed default layout not working in 0.2.30

Multiple changes in 0.2.31.
- several bug fixes
- the input dir is now not cluttered with json dumps. the json dumps can be set to true via json_dump_status in pixboards.boardmakers. planned future support for the dump status to be triggered by an argument.

Changes in 0.2.33
- descending boards sort by image metadata properly now
- layout and column settings work on local html files too (due to saving settings as cookies AND localstorage.)

Changes in 1.0.1
- big internal refactor: nothing runs at import time; `pixboards` / `python -m pixBoards` return proper exit codes
- justified layout rewritten: rows fill the width edge to edge, nothing is cropped, the last row isn't stretched, and image sizes are known before they load
- board pages: sticky toolbar, lightbox (click an image; Shift+click copies its link), keyboard shortcuts (←/→ pages, R random page, J layout), row-height slider, back-to-top, working jump-to-page, "Random Page" button above the grid
- index: thumbnails, collapsible folders, search box
- optional "open on Pinterest" links for gallery-dl downloads (`pinterest_<pinId>` file names): a toolbar toggle, a hover badge, a lightbox link and the P key; off by default (`source_links: true` turns it on)
- much faster re-runs: hashes, image sizes and dates are cached in `~/.cache/pixboards`, so only new or changed files are read (a warm run over ~5000 images takes about 0.3 s)
- uploads: links always line up with their files, each upload is saved immediately, database errors roll back, requests time out, real MIME types
- `--recent N` keeps the newest N (EXIF date, else file time); `--reddit` sorts by reddit post id; `--gitPush` works and never exposes the token
- new config keys: `default_layout`, `row_height` (was `height`), `lazy_loading`, `source_links`, `json_dump`, `cache_file`; `~` and `$VARS` work in paths
- packaging: `pyproject.toml` (Python 3.10+); database/upload dependencies are optional (`pip install "pixboards[upload]"`); tests and CI
- the repo is Linux-first: `scripts/publish.sh` and `scripts/release.sh` replace the Windows batch files; `gui.py` and `main.py` are gone
- details in [docs/1.0.1-report.md](docs/1.0.1-report.md), next steps in [docs/1.0.1-plan.md](docs/1.0.1-plan.md)

# pixBoards

pixBoards is a python library to help you organise your images and videos into masonry-containers (the pinterest layout)

It outputs simple html files with links to the images. Simplicity was the aim here, so don't expect fancy stuff in it.

It organises the images into "boards" which can be nested inside other boards. (Just think of them as a folder for now)

You can also automatically upload the files to imgchest and use those links in the output html files. You can then simply host these output files and you will have a working webpage. (If you had to use local files, you'd have to host the images too, which would be a pain in) (use --upload for that)

you can also use lists of imagelinks to create boards.

I also recently added the ability to use links in sidecarfiles to use as upload links instead of uploading the image to imgchest. (if you used a bulk downloader like gallery-dl, you'd be able to easily create such sidecar files every time you download.)

### screenshots

example of index file
![https://cdn.imgchest.com/files/4apc5px5gv4.png](https://cdn.imgchest.com/files/4apc5px5gv4.png)

example of image board
![https://cdn.imgchest.com/files/yrgcnjaxew4.png](https://cdn.imgchest.com/files/yrgcnjaxew4.png)

## how to use 

create a config with `pixboards --makeConfig` (it never overwrites an existing config.yml), or copy config_example.yml to config.yml, and set `masterDir` and `directories`.

if you wish to upload to imgchest and use those links instead, use `--upload`. uploading needs a running postgresql server, `IMG_CHEST_API_KEY` in a `.env` file, and the upload extra (below).

### install

`pip install pixboards` (html boards only) or `pip install "pixboards[upload]"` (adds postgres, imgchest and .env support)

or clone the repo and install it in editable mode:

```
git clone https://github.com/flynnsharwood/pixBoards.git
cd pixBoards
pip install -e ".[upload,test]"
pytest
```

### First time upload
If you have a LOT of files to upload for the first time, use the bulk uploader instead: [imgUploader](https://github.com/flynnsharwood/imgUploader). It uploads in posts of 20 images and caches the links and hashes in the same postgres table pixBoards reads. (Plans to merge it into pixBoards are in [docs/1.0.1-plan.md](docs/1.0.1-plan.md).)

### Usage
`pixboards` (when installed) or `python3 -m pixBoards` (from the repo)

flags you might use

`--config` change the config file being used

`--upload` use imgchest links (uploads files that aren't in the link cache yet). `--useSaved` only uses links already cached, `--sidecar` uses the link in `<image>.<ext>.txt` files

`--recent N` / `--random N` add a "recent imgs" / "randomised_set" board (`-1` = all images). `--reddit` sorts the recent board by reddit post id

`--gitPush` push the output folder to a github repo (`remote_url` and `gitUsername` in the config, `GITHUB_PAT` in the environment or `.env`). set up your repo to trigger a gh_pages deployment every push.

`--dir`, `--col`, `--height`, `--pageSize` override the config for one run

logs are written to `logs/` in the folder you run from. hashes, image sizes and dates are cached in `~/.cache/pixboards/media.sqlite3` (change with `cache_file`).

### On the board pages
- click an image to open it large (←/→ to move, Esc to close); Shift+click copies its link (or its hash for uploaded images)
- ←/→ previous/next page, R random page, J switch between masonry and justified
- the column count (masonry) and row height (justified) are remembered per browser; `default_layout` in the config sets the starting layout
- for Pinterest downloads made with gallery-dl, tick "Pinterest links" in the toolbar to get a "↗ Pinterest" badge on each image (on hover) and an "open on Pinterest" link in the lightbox (or press P there). It's remembered per browser; `source_links: true` in the config makes it start on

### Pinterest boards made with gallery-dl
pixBoards 1.0.1 was developed and tested on Pinterest boards downloaded with [gallery-dl](https://github.com/mikf/gallery-dl), a command-line downloader for image sites (about 5,000 images in 60 folders), and the "open on Pinterest" links are built for its file names.

1. Download your boards, for example:

   ```
   gallery-dl --cookies cookies.txt https://www.pinterest.com/<your-user>/
   ```

   gallery-dl saves every pin as `pinterest_<pinId>.<ext>` (sometimes `pinterest_<pinId>_<n>.<ext>`), in one folder per board (and section).
2. Add that download folder to `directories` in your config and run pixBoards as usual. Each Pinterest board becomes a pixBoards board, and sections become nested boards.
3. pixBoards reads the pin id from each file name and links the image to its original pin, `https://www.pinterest.com/pin/<pinId>/`. The links are hidden by default: tick **Pinterest links** in the page toolbar (remembered per browser), or set `source_links: true` in the config to have them on from the start. Then each image shows a "↗ Pinterest" badge on hover, and the lightbox has an "open on Pinterest" link (or press **P**).

Notes:
- Only the file name is used, so keep gallery-dl's default naming. Renamed files simply get no link; everything else works the same.
- This also works for `--upload` boards (the local file name is still known) and for image lists whose URLs end in `pinterest_<pinId>.<ext>`.
- `--sidecar` reads a link from `<image>.<ext>.txt` next to each image. gallery-dl doesn't write those by default, but its `metadata` post-processor can be configured to (one file per image, containing the link).

### Publishing several boards
`scripts/publish.sh` builds named profiles and pushes their upload build to GitHub Pages repos. Copy `scripts/publish.conf.example` to `scripts/publish.conf` (git-ignored) and edit it, then run for example `scripts/publish.sh -u pinterest` or `scripts/publish.sh -u -d all`. Use `-n` for a dry run.

### Releasing
`scripts/release.sh -n` builds and checks the package; `scripts/release.sh` also uploads the version in `pixBoards/__init__.py` to PyPI and tags it. Publishing a GitHub release does the same through `.github/workflows/publish.yml` (PyPI trusted publishing).


here is a link to an example board - [https://flynnsharwood.github.io/exampleBoard/index.html](https://flynnsharwood.github.io/exampleBoard/index.html) 

---
## Task list

From the code review of Nov 2026. Everything chosen for 1.0.1 is done; what's left is
below. The detailed plan, including imgUploader and the database design, is in
[docs/1.0.1-plan.md](docs/1.0.1-plan.md), and what changed is in [docs/1.0.1-report.md](docs/1.0.1-report.md).

### Open
- [ ] Recreate the remaining `scripts/publish.conf` profile configs (`configs/example.yml`, `reddit.yml`, `main.yml`) with Linux paths (`configs/pinterest.yml` exists), then run `scripts/publish.sh -u pinterest` once
- [ ] Click through the lightbox, keyboard shortcuts and the Pinterest-links toggle in a desktop browser (so far checked in code and headless screenshots)
- [ ] Add pixBoards as a trusted publisher on PyPI (needed by the publish workflow)
- [ ] Storage layer: one module owning all SQL, the unified schema with migrations, a `boards` table replacing `savedBoards` (plan section 3)
- [ ] Merge imgUploader as a `pixboards-upload` bulk command with 20 images per imgchest post (plan section 2)
- [ ] Index page looks uncanny: the 40px thumbnails squeezed between the counts and names of a text tree are too small to recognise and make the list look cluttered. Proposal: a left/right split, with the board tree (names, counts, collapsible folders, search) in a sticky left column and a grid of board cards on the right, each with a large thumbnail (about 200px, or a 2x2 collage of the board's first images) and the board name and count below it. Clicking a folder in the tree shows its boards on the right; on phones the two panes stack (plan section 1)
- [ ] HEIC files are listed but browsers (except Safari) can't show them; convert or skip them
- [ ] Video sizes aren't known before they load (no ffprobe); justified rows with videos adjust once metadata arrives

### Done in 1.0.1
- [x] Tested against PostgreSQL 18: real `--upload` (and a quota refusal on the old imgchest account), cached links on re-runs, `--sidecar`, `--useSaved`, `--saveBoards`, an old-style table, an unreachable server
- [x] Old link cache (5,009 rows) imported from Aiven into the local database; 3,660 of 4,951 test images found by `--useSaved`
- [x] `pixboards` command installed with `pipx install --editable ".[upload]"`
- [x] Quick fixes: `--makeConfig` overwrite, `--saveBoards` NameError, empty hash map, Linux paths, missing Pillow, token leak
- [x] No work at import time; config passed as parameters; one DB connection; `--gitPush` works
- [x] Upload & DB: links aligned with files (`MediaItem`), rollback on errors, commit after each upload, narrower excepts, timeouts, MIME types, `sql.Identifier`, batched lookups, no wasted sidecar query, skipped-images log in `logs/`
- [x] `--recent N` truncates, EXIF dates read correctly (the old lookup searched the wrong EXIF section and never found them), upload boards sort by their local files, `--reddit` implemented
- [x] Pagination & escaping: all HTML in autoescaped Jinja templates; First/Last/prev/next links; jump-to-page fixed
- [x] Performance: local cache of hashes/sizes/dates, folders resolved once, lazy imports, one template render per page
- [x] Justified layout rewritten (row maths, no cropping, capped scale-up, last row, rounding, relayout on load, `data-ar`, same margins as masonry)
- [x] Broken-now fixes: invalid CSS, charset/viewport meta, `<hr></hr>`, video `preload`/`type`, no video backgrounds, clipboard fallback
- [x] Interaction: lightbox, keyboard shortcuts, sticky toolbar, `default_layout`, row-height slider, back-to-top, jump-to-page
- [x] "Open on Pinterest" links: pin id from gallery-dl file names, `source_links` config key (off by default), toolbar toggle, hover badge, lightbox link, P key
- [x] Index: search, thumbnails, collapsible boards, count style in CSS; lazy loading + `decoding="async"` by default; filename alt text
- [x] Code cleanup: dead code and commented-out code removed, one media extension list, imports at the top, ruff lint + format
- [x] Renames: `Board` / `Page`, `page.board`, no `hash` shadowing
- [x] `pyproject.toml` with dynamic version and `[upload]` / `[test]` extras; `setup.py`, `MANIFEST.in`, `requirements.txt` removed
- [x] pytest suite (44 tests) and a GitHub Actions workflow (lint, tests on Python 3.10 and 3.13, build); Python 3.10 or newer is required; publish workflow on v4/v5 with trusted publishing
- [x] Repo cleanup: Windows files, old profiles, build output, stale files, personal configs moved to `archive/` (git-ignored); `gui.py`, `fib_tabbing.py`, `main.py` removed; `.gitattributes`
