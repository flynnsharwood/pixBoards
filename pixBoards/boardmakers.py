"""Build Board objects from folders, image lists, uploads, and the
random / recent meta-boards."""

from __future__ import annotations

import json
import logging
import os
import random
import re
from pathlib import Path
from typing import Iterator, List, Tuple

from pixBoards.classes import NEST_SEPARATOR, Board
from pixBoards.media import MediaItem, is_media

logger = logging.getLogger(__name__)

RANDOM_BOARD = "randomised_set"
RECENT_BOARD = "recent imgs"


def scan_directories(directories) -> Iterator[Tuple[str, List[Path]]]:
    """Yield (board name, sorted media files) for every folder under each
    directory, including folders without media (they become sub-indexes).

    Each top-level directory is resolved once; paths below it are built by
    joining, which avoids a resolve() per file (20 s of a 53 s run in the
    old profiles)."""
    for d in directories:
        src = Path(os.path.expandvars(str(d))).expanduser()
        if not src.is_dir():
            logger.warning(f"Skipping non-existent directory: {src}")
            continue
        src = src.resolve()
        base = src.parent
        for root, dirs, files in os.walk(src):
            dirs.sort()
            root_path = Path(root)
            media = [root_path / f for f in sorted(files) if is_media(f)]
            name = str(root_path.relative_to(base)).replace(os.sep, NEST_SEPARATOR)
            logger.debug(f"Processing {root} with {len(media)} media files.")
            yield name, media


def add_local_info(items: List[MediaItem], cache):
    """Fill width/height/timestamp from the local file (cached)."""
    with_path = [i for i in items if i.path is not None]
    if not with_path:
        return
    info = cache.info([i.path for i in with_path])
    for item in with_path:
        if item.path in info:
            item.width, item.height, item.timestamp = info[item.path]


def standardBoards(directories, output_dir, cache) -> List[Board]:
    boards = []
    for name, files in scan_directories(directories):
        items = [MediaItem(src=p.as_uri(), path=p) for p in files]
        add_local_info(items, cache)
        boards.append(Board(name, output_dir, items, dummy=not files))
    return boards


def uploadBoards(
    directories, output_dir, conn, config, cache, use_sidecar=False, use_saved=False, uploader=None
):
    from pixBoards.imgchest import SKIPPED_LOG, Uploader, ensure_cache_table, process_images

    uploader = uploader or Uploader()  # one per run: stops after imgchest refuses uploads
    table = config["tableName"]
    ensure_cache_table(conn, table)
    boards = []
    total = linked = failed_folders = 0
    for name, files in scan_directories(directories):
        if not files:
            boards.append(Board(name, output_dir, [], dummy=True))
            continue
        total += len(files)
        logger.debug(f"Resolving links for {len(files)} files in {name}")
        try:
            items = process_images(
                files,
                conn,
                table,
                cache,
                use_sidecar=use_sidecar,
                use_saved=use_saved,
                uploader=uploader,
            )
        except Exception as e:  # DB error: already rolled back; skip this folder
            logger.error(f"Failed to process {name}: {e}")
            failed_folders += 1
            continue
        linked += len(items)
        add_local_info(items, cache)
        boards.append(Board(name, output_dir, items))
        logger.debug(f"Uploaded board created: {name} ({len(items)} images)")
    skipped = total - linked
    logger.info(
        f"upload boards: {linked} of {total} files linked "
        f"({uploader.uploaded} newly uploaded, {linked - uploader.uploaded} already linked)"
        + (f", {skipped} skipped (see {SKIPPED_LOG})" if skipped else "")
        + (f", {failed_folders} folder(s) failed" if failed_folders else "")
    )
    if uploader.blocked:
        logger.error(
            f"Uploads were refused by imgchest ({uploader.blocked}); boards only contain "
            f"images that were already uploaded. See {SKIPPED_LOG}."
        )
    return boards


def boardsForImglist(list_files, output_dir) -> List[Board]:
    boards = []
    for list_file in list_files:
        name = os.path.splitext(os.path.basename(list_file))[0]
        with open(list_file, "r", encoding="utf-8") as f:
            items = [MediaItem(src=line.strip()) for line in f if line.strip()]
        boards.append(Board(name, output_dir, items, from_list=True))
    return boards


def _all_items(boards) -> List[MediaItem]:
    """Every item of every board, de-duplicated by link (first one wins)."""
    seen = {}
    for b in boards:
        for item in b.items:
            seen.setdefault(item.src, item)
    return list(seen.values())


def randomBoard(boards, count, output_dir) -> Board:
    """``count`` random items; a negative count (or one larger than the
    number of items) shuffles everything."""
    items = _all_items(boards)
    if 0 < count < len(items):
        items = random.sample(items, count)
    else:
        random.shuffle(items)
    logger.info(f"random board: {len(items)} of {len(_all_items(boards))} images")
    return Board(RANDOM_BOARD, output_dir, items)


def reddit_sort_key(item: MediaItem) -> int:
    """Reddit downloads start with the post id (base 36) followed by a space."""
    prefix = re.split(r"(?:\s|%20)", item.name, maxsplit=1)[0]
    try:
        return int(prefix, 36)
    except ValueError:
        return -1


def descBoard(boards, count, output_dir, reddit=False) -> Board:
    """Newest first: by EXIF DateTimeOriginal / file time, or by reddit post
    id with ``reddit=True``. ``count > 0`` keeps only the newest ``count``;
    ``-1`` keeps everything. Items without a local file go last."""
    items = _all_items(boards)
    if reddit:
        items.sort(key=reddit_sort_key, reverse=True)
    else:
        items.sort(
            key=lambda i: i.timestamp if i.timestamp is not None else float("-inf"), reverse=True
        )
    if count > 0:
        items = items[:count]
    return Board(RECENT_BOARD, output_dir, items)


def dump_json(boards, path):
    """Write {board name: [{path, src}, ...]} for every board."""
    data = {
        b.name: [{"path": str(i.path) if i.path else None, "src": i.src} for i in b.items]
        for b in boards
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"wrote {path}")
