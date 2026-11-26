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
- [ ] Finish uploading the Pinterest test library: about 1,500 files are left. imgchest allows about 250 an hour per connection, so they are going to catbox instead (`imguploader upload --host catbox --wait`). Then rebuild with `pixboards --config configs/pinterest.yml --upload --useSaved`
- [ ] Copy imguploader's `accounts` listing into pixBoards (or share the code once the repos merge)

## Long term (3.0.0 / 4.0.0)
Ideas for making uploads always possible, from the Nov 2026 upload test. imgchest allowed about 250
uploads an hour per connection, and catbox returned frequent empty replies. Nothing here is
started; the current hosts stay as they are until then.
- [ ] **Your own storage bucket as the main host (3.0.0).** Use an S3-compatible bucket you
      control: Cloudflare R2 (about 10 GB free, no fee when images are viewed; use a custom domain,
      since `r2.dev` is rate-limited) or Backblaze B2 behind Cloudflare. It has no hourly cap and no
      third-party quota, and you choose the file names (for example the MD5). One S3 backend covers
      R2, B2, Wasabi and MinIO.
- [ ] **Hosts tried in order (3.0.0).** Upload to the bucket first and use imgchest and catbox
      only as fallbacks. The `account` column already records where each link lives.
- [ ] **Thumbnails (3.0.0).** With your own bucket, upload a small thumbnail next to each image and
      have board pages load those.
- [ ] **Moving links between hosts (4.0.0).** Links are looked up by MD5, so a tool could copy
      files from one host to another and rewrite `image_cache` while boards keep working.
- [ ] **Mirror links in pixBoards (4.0.0).** imguploader now keeps an `image_mirrors` table
      (merged from mirrorMaintainer, Nov 2026): every known copy of an image, tagged with its host,
      including Pinterest originals (`i.pinimg.com/originals/...`) imported from gallery-dl
      metadata. pixBoards doesn't read it yet. Next: write a page's mirror links into
      `data-mirrors` and switch to the next one when an image fails to load.
- [ ] **Other free hosts as extra fallbacks**, only if they have an official upload API:
      - imgbb: 32 MB per file, images only;
      - pixeldrain: free files expire when nobody views them.

      Avoid Imgur (removed adult content, deletes inactive uploads) and hosts without an API
      (Postimages, ImgBox). Cloudinary and ImageKit don't allow adult content.
- [ ] **Hosting it yourself:** a small server with nginx, or a home machine shared through
      Cloudflare Tunnel. Full control, but you have to keep it running.

## Done after 1.0.1
- [x] Several imgchest accounts, one API key each, with failover (401/403 move on to the next account); `--account`, `imgchest_accounts`; links record their account
- [x] Full accounts are flagged in the `imgchest_accounts` table (keyed by a key fingerprint, shared by both tools). A storage refusal sets the flag automatically, `imguploader accounts --flag-full/--unflag` sets or clears it by hand, and flagged accounts are skipped. Account `hlsdfd` is flagged (over its 10 GB)
- [x] Schema upgrades only lock `image_cache` when a column is missing (fixed a deadlock with a running imguploader)
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
