"""Local cache of per-file metadata (MD5, image size, timestamp).

Entries are keyed by absolute path and are only trusted while the file's size
and modification time are unchanged, so edited files are re-read
automatically. Profiling showed that hashing every file on every upload run
took ~85% of the run time; with this cache only new or changed files are
hashed.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

_FIELDS = ("md5", "width", "height", "taken")
_EXIF_IFD = 0x8769
_DATETIME_ORIGINAL = 36867
_DATETIME = 306


def default_cache_path() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return Path(base) / "pixboards" / "media.sqlite3"


def compute_md5(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def read_image_info(path: Path, mtime: float) -> Tuple[Optional[int], Optional[int], float]:
    """(width, height, timestamp). Timestamp is EXIF DateTimeOriginal when
    present, otherwise the file's modification time. Only the file header is
    read. Files Pillow can't open (videos, HEIC without a plugin) get no size."""
    try:
        from PIL import Image

        with Image.open(path) as img:
            width, height = img.size
            exif = img.getexif()
            raw = exif.get_ifd(_EXIF_IFD).get(_DATETIME_ORIGINAL) or exif.get(_DATETIME)
    except Exception:  # not an image Pillow understands: fall back to mtime
        return None, None, mtime

    taken = mtime
    if isinstance(raw, str):
        try:
            taken = datetime.strptime(raw.strip("\x00 "), "%Y:%m:%d %H:%M:%S").timestamp()
        except ValueError:
            pass
    return width, height, taken


class MediaCache:
    """``with MediaCache(path) as cache: cache.hashes(paths); cache.info(paths)``"""

    def __init__(self, db_path=None, workers: Optional[int] = None):
        self.db_path = Path(db_path) if db_path else default_cache_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.workers = workers or min(8, (os.cpu_count() or 2) * 2)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS media (
                   path TEXT PRIMARY KEY,
                   size INTEGER NOT NULL,
                   mtime_ns INTEGER NOT NULL,
                   md5 TEXT,
                   width INTEGER,
                   height INTEGER,
                   taken REAL
               )"""
        )

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
            self.conn = None

    # --- internals -------------------------------------------------------
    def _load(self, paths: List[Path]) -> Dict[Path, dict]:
        """Current rows for ``paths``; stale or missing entries have None fields."""
        stats = {}
        for p in paths:
            try:
                st = p.stat()
            except OSError:
                continue
            stats[p] = st

        rows: Dict[str, tuple] = {}
        keys = [str(p) for p in stats]
        for i in range(0, len(keys), 500):
            chunk = keys[i : i + 500]
            marks = ",".join("?" * len(chunk))
            for row in self.conn.execute(
                f"SELECT path, size, mtime_ns, md5, width, height, taken FROM media WHERE path IN ({marks})",
                chunk,
            ):
                rows[row[0]] = row

        entries = {}
        for p, st in stats.items():
            row = rows.get(str(p))
            fresh = row is not None and row[1] == st.st_size and row[2] == st.st_mtime_ns
            entry = {"size": st.st_size, "mtime_ns": st.st_mtime_ns, "mtime": st.st_mtime}
            entry.update(dict(zip(_FIELDS, row[3:])) if fresh else dict.fromkeys(_FIELDS))
            entries[p] = entry
        return entries

    def _store(self, entries: Dict[Path, dict]):
        self.conn.executemany(
            """INSERT OR REPLACE INTO media (path, size, mtime_ns, md5, width, height, taken)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                (str(p), e["size"], e["mtime_ns"], e["md5"], e["width"], e["height"], e["taken"])
                for p, e in entries.items()
            ],
        )
        self.conn.commit()

    def _map(self, func, items):
        if len(items) < 4:
            return [func(x) for x in items]
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            return list(pool.map(func, items))

    # --- public API ------------------------------------------------------
    def hashes(self, paths: Iterable[Path]) -> Dict[Path, str]:
        """MD5 for each readable path; only new or changed files are hashed."""
        entries = self._load(list(paths))
        todo = [p for p, e in entries.items() if e["md5"] is None]
        if todo:
            logger.info(f"hashing {len(todo)} new or changed file(s)")
            results = self._map(_safe(compute_md5), todo)
            for p, md5 in zip(todo, results):
                entries[p]["md5"] = md5
            self._store({p: entries[p] for p in todo})
        return {p: e["md5"] for p, e in entries.items() if e["md5"]}

    def info(self, paths: Iterable[Path]) -> Dict[Path, Tuple[Optional[int], Optional[int], float]]:
        """(width, height, timestamp) for each readable path."""
        entries = self._load(list(paths))
        todo = [p for p, e in entries.items() if e["taken"] is None]
        if todo:
            logger.debug(f"reading image info for {len(todo)} file(s)")
            results = self._map(lambda p: read_image_info(p, entries[p]["mtime"]), todo)
            for p, (w, h, taken) in zip(todo, results):
                entries[p].update(width=w, height=h, taken=taken)
            self._store({p: entries[p] for p in todo})
        return {p: (e["width"], e["height"], e["taken"]) for p, e in entries.items()}


def _safe(func):
    def wrapper(p):
        try:
            return func(p)
        except OSError as e:
            logger.warning(f"could not read {p}: {e}")
            return None

    return wrapper
