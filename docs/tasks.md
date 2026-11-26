# Task list

From the code review of Nov 2026. Everything chosen for 1.0.1 is done; what's left is
below. The detailed plan, including imgUploader and the database design, is in
[docs/1.0.1-plan.md](1.0.1-plan.md), and what changed is in [docs/1.0.1-report.md](1.0.1-report.md).

## Open
- [ ] Recreate the remaining `scripts/publish.conf` profile configs (`configs/example.yml`, `reddit.yml`, `main.yml`) with Linux paths (`configs/pinterest.yml` exists), then run `scripts/publish.sh -u pinterest` once
- [ ] Click through the lightbox, keyboard shortcuts and the Pinterest-links toggle in a desktop browser (so far checked in code and headless screenshots)
- [ ] Add pixBoards as a trusted publisher on PyPI (needed by the publish workflow; 1.0.1 was uploaded by hand)
- [ ] Storage layer: one module owning all SQL, the unified schema with migrations, a `boards` table replacing `savedBoards` (plan section 3)
- [ ] Merge imgUploader as a `pixboards-upload` bulk command with 20 images per imgchest post (plan section 2). imgUploader has since been refactored into a tested `imguploader` package with the same `image_cache` schema, which makes a merge straightforward (plan section 2, "Update")
- [ ] Index page looks uncanny: the 40px thumbnails squeezed between the counts and names of a text tree are too small to recognise and make the list look cluttered. Proposal: a left/right split, with the board tree (names, counts, collapsible folders, search) in a sticky left column and a grid of board cards on the right, each with a large thumbnail (about 200px, or a 2x2 collage of the board's first images) and the board name and count below it. Clicking a folder in the tree shows its boards on the right; on phones the two panes stack (plan section 1)
- [ ] HEIC files are listed but browsers (except Safari) can't show them; convert or skip them
- [ ] Video sizes aren't known before they load (no ffprobe); justified rows with videos adjust once metadata arrives
- [ ] Finish uploading the Pinterest test library: about 1,520 files were left after the first run (imgchest allows about 250 an hour); `imguploader upload --wait` is working through them, then rebuild with `pixboards --config configs/pinterest.yml --upload`

## Done after 1.0.1
- [x] imgchest's hourly upload limit (HTTP 429) stops uploads for the run instead of failing every remaining file
- [x] A config without database keys no longer crashes `--upload`; defaults match `config_example.yml`, and without a password libpq's `PGPASSWORD` or `~/.pgpass` is used
- [x] README rewritten; release notes moved to `CHANGELOG.md`, the task list to this file

## Done in 1.0.1
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
