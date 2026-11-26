"""Upload to imgchest and cache the links in PostgreSQL by MD5 hash."""

from __future__ import annotations

import functools
import logging
import mimetypes
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from pixBoards.media import MediaItem

logger = logging.getLogger(__name__)

API_URL = "https://api.imgchest.com/v1/post"
TIMEOUT = (10, 300)  # connect, read (seconds)
SKIPPED_LOG = os.path.join("logs", "skipped_images.log")


class UploadError(Exception):
    """One file could not be uploaded."""


class UploadsBlocked(UploadError):
    """imgchest refuses all uploads (e.g. storage quota exceeded, bad key)."""


@functools.lru_cache(maxsize=None)
def _headers():
    try:
        from dotenv import find_dotenv, load_dotenv

        load_dotenv(find_dotenv(usecwd=True))  # .env in the folder you run from
    except ImportError:  # python-dotenv is optional; plain env vars still work
        pass
    key = os.getenv("IMG_CHEST_API_KEY")
    if not key:
        raise UploadError("IMG_CHEST_API_KEY is not set (environment or .env)")
    return {"Authorization": f"Bearer {key}"}


def _api_error(resp) -> str:
    """imgchest's own error message, e.g. the storage quota text."""
    try:
        body = resp.json()
        message = body.get("error") or body.get("message")
    except ValueError:
        message = None
    return f"{resp.status_code} {message or resp.reason}"


def upload_image(image_path: Path) -> str:
    """Upload one file as an imgchest post and return its direct link.

    Raises UploadsBlocked when imgchest refuses uploads altogether
    (401/403: bad key, storage quota; 429: hourly upload limit), UploadError
    for anything else."""
    import requests

    mime = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                API_URL,
                headers=_headers(),
                files={"images[]": (image_path.name, f, mime)},
                data={"title": image_path.name},
                timeout=TIMEOUT,
            )
        if resp.status_code in (401, 403, 429):
            raise UploadsBlocked(_api_error(resp))
        if not resp.ok:
            raise UploadError(_api_error(resp))
        post_id = resp.json()["data"]["id"]

        info = requests.get(f"{API_URL}/{post_id}", headers=_headers(), timeout=TIMEOUT)
        if not info.ok:
            raise UploadError(_api_error(info))
        images = info.json()["data"]["images"]
    except (requests.RequestException, KeyError, ValueError) as e:
        raise UploadError(str(e)) from e
    if not images:
        raise UploadError("no images returned in response")
    return images[0]["link"]


class Uploader:
    """Wraps an upload function for one run. After imgchest refuses uploads
    altogether, later calls fail immediately instead of sending every file."""

    def __init__(self, upload=upload_image):
        self.upload = upload
        self.blocked: Optional[str] = None
        self.uploaded = 0

    def __call__(self, path: Path) -> str:
        if self.blocked:
            raise UploadError(f"uploads stopped earlier in this run: {self.blocked}")
        try:
            link = self.upload(path)
            self.uploaded += 1
            return link
        except UploadsBlocked as e:
            self.blocked = str(e)
            logger.error(f"imgchest refused the upload ({e}); not uploading anything else this run")
            raise


# --- database helpers (all SQL for the link cache lives here) ------------------
def _table(table_name):
    from psycopg2 import sql

    return sql.Identifier(table_name)


def ensure_cache_table(conn, table_name):
    from psycopg2 import sql

    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """CREATE TABLE IF NOT EXISTS {} (
                       hash TEXT PRIMARY KEY,
                       link TEXT NOT NULL,
                       filename TEXT,
                       uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                   )"""
            ).format(_table(table_name))
        )
        # older tables were created without uploaded_at
        cur.execute(
            sql.SQL(
                "ALTER TABLE {} ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
            ).format(_table(table_name))
        )
    conn.commit()


def lookup_links(conn, table_name, hashes: Iterable[str]) -> Dict[str, str]:
    from psycopg2 import sql

    hashes = list(hashes)
    if not hashes:
        return {}
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("SELECT hash, link FROM {} WHERE hash = ANY(%s)").format(_table(table_name)),
            (hashes,),
        )
        return dict(cur.fetchall())


def save_link(conn, table_name, hash_val, link, filename, keep_existing_link=True):
    """Insert a link; an existing row keeps its link (unless told otherwise)
    and only gets a filename if it had none."""
    from psycopg2 import sql

    link_update = "{t}.link" if keep_existing_link else "EXCLUDED.link"
    query = sql.SQL(
        """INSERT INTO {t} (hash, link, filename) VALUES (%s, %s, %s)
           ON CONFLICT (hash) DO UPDATE SET
               link = """
        + link_update
        + """,
               filename = COALESCE({t}.filename, EXCLUDED.filename)"""
    ).format(t=_table(table_name))
    with conn.cursor() as cur:
        cur.execute(query, (hash_val, link, filename))


def backfill_filenames(conn, table_name, pairs):
    """Set filename where it is missing. ``pairs`` = [(filename, hash), ...]"""
    from psycopg2 import sql

    if not pairs:
        return
    with conn.cursor() as cur:
        cur.executemany(
            sql.SQL(
                "UPDATE {} SET filename = %s WHERE hash = %s AND (filename IS NULL OR filename = '')"
            ).format(_table(table_name)),
            pairs,
        )


# --- sidecar files ----------------------------------------------------------
def sidecar_link(image_path: Path) -> Optional[str]:
    """First line of ``<image>.<ext>.txt`` if it is an http(s) link."""
    sidecar = image_path.with_name(image_path.name + ".txt")
    try:
        with sidecar.open("r", encoding="utf-8") as f:
            line = f.readline().strip()
    except FileNotFoundError:
        return None
    except OSError as e:
        logger.warning(f"Failed to read sidecar file {sidecar}: {e}")
        return None
    return line if line.startswith(("http://", "https://")) else None


# --- main entry point -------------------------------------------------------
def process_images(
    image_paths: List[Path],
    conn,
    table_name: str,
    cache,
    use_sidecar: bool = False,
    use_saved: bool = False,
    skipped_log_file=SKIPPED_LOG,
    uploader=upload_image,
) -> List[MediaItem]:
    """Resolve every file to a hosted link, in the order given.

    Order of preference: sidecar link (with --sidecar), cached link (by MD5),
    fresh upload (unless --useSaved). Files that end up without a link are
    left out and written to ``skipped_log_file``. Each upload is committed
    straight away, so a later failure never loses links that were uploaded.
    Database errors roll back and propagate to the caller.
    """
    hashes = cache.hashes(image_paths)
    try:
        cached = lookup_links(conn, table_name, set(hashes.values()))
    except Exception:
        conn.rollback()
        raise

    items: List[MediaItem] = []
    skipped = []
    backfill = []

    for path in image_paths:
        hash_val = hashes.get(path)
        if hash_val is None:
            skipped.append((path, "could not be read"))
            continue

        link = None
        try:
            if use_sidecar:
                link = sidecar_link(path)
                if link:
                    save_link(conn, table_name, hash_val, link, path.name)
                    conn.commit()

            if link is None and hash_val in cached:
                link = cached[hash_val]
                backfill.append((path.name, hash_val))

            if link is None and not use_saved:
                try:
                    link = uploader(path)
                except UploadError as e:
                    skipped.append((path, f"upload failed: {e}"))
                    continue
                save_link(conn, table_name, hash_val, link, path.name)
                conn.commit()
                logger.debug(f"uploaded {path} -> {link}")
        except Exception:
            conn.rollback()
            raise

        if link is None:
            skipped.append((path, "not in the cache (--useSaved)"))
            continue
        items.append(MediaItem(src=link, path=path, hash=hash_val))

    try:
        backfill_filenames(conn, table_name, backfill)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    if skipped:
        os.makedirs(os.path.dirname(skipped_log_file) or ".", exist_ok=True)
        with open(skipped_log_file, "a", encoding="utf-8") as f:
            for p, reason in skipped:
                f.write(f"{p} -> {reason}\n")
        logger.debug(f"{len(skipped)} image(s) skipped, see {skipped_log_file}")

    return items
