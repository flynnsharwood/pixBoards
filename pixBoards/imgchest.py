"""Upload to imgchest and cache the links in PostgreSQL by MD5 hash."""

from __future__ import annotations

import logging
import mimetypes
import os
import re
from dataclasses import dataclass
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
    """imgchest refuses uploads: bad key (401), account refused or over its storage (403),
    hourly limit (429)."""

    def __init__(self, msg: str, status: int | None = None):
        super().__init__(msg)
        self.status = status


# --- API keys and accounts ----------------------------------------------------
# Same convention as imguploader:
#   IMG_CHEST_API_KEY                 the "default" account
#   IMG_CHEST_API_KEY_<ACCOUNT>       a named account
#   IMG_CHEST_API_KEY_<ACCOUNT>_<N>   more keys for that account (a bare number: the default one)
#   IMG_CHEST_ACCOUNTS=main,alt       order to try the accounts in (or --account / imgchest_accounts)
KEY_PREFIX = "IMG_CHEST_API_KEY"
DEFAULT_ACCOUNT = "default"
_KEY_VAR = re.compile(rf"^{KEY_PREFIX}(?:_(?P<label>[A-Za-z0-9_]+))?$")


@dataclass(frozen=True)
class ApiKey:
    account: str
    var: str
    token: str


def _load_dotenv():
    try:
        from dotenv import find_dotenv, load_dotenv

        load_dotenv(find_dotenv(usecwd=True))  # .env in the folder you run from
    except ImportError:  # python-dotenv is optional; plain env vars still work
        pass


def _account_of(label: Optional[str]) -> str:
    name = re.sub(r"_\d+$", "", label or "")
    return name.lower() if name and not name.isdigit() else DEFAULT_ACCOUNT


def load_keys(environ=None, only: Optional[List[str]] = None) -> List[ApiKey]:
    """Configured keys in the order to try them; ``only`` limits and orders the accounts."""
    environ = os.environ if environ is None else environ
    keys = [
        ApiKey(_account_of(m.group("label")), var, token.strip())
        for var, token in environ.items()
        if (m := _KEY_VAR.match(var)) and token.strip()
    ]
    wanted = [a.strip().lower() for a in only or [] if a.strip()]
    if wanted:
        unknown = set(wanted) - {k.account for k in keys}
        if unknown:
            raise UploadError(f"no imgchest API key for account(s): {', '.join(sorted(unknown))}")
        keys = [k for k in keys if k.account in wanted]
    else:
        wanted = [
            a.strip().lower() for a in environ.get("IMG_CHEST_ACCOUNTS", "").split(",") if a.strip()
        ]

    def natural(var):
        return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", var)]

    def rank(k):
        pos = wanted.index(k.account) if k.account in wanted else len(wanted)
        return (pos, k.account != DEFAULT_ACCOUNT, k.account, natural(k.var))

    return sorted(keys, key=rank)


def _api_error(resp) -> str:
    """imgchest's own error message, e.g. the storage quota text."""
    try:
        body = resp.json()
        message = body.get("error") or body.get("message")
    except ValueError:
        message = None
    return f"{resp.status_code} {message or resp.reason}"


def upload_image(image_path: Path, token: str) -> str:
    """Upload one file as an imgchest post and return its direct link.

    Raises UploadsBlocked when imgchest refuses the key, the account or the
    connection (401/403/429), UploadError for anything else."""
    import requests

    headers = {"Authorization": f"Bearer {token}"}
    mime = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                API_URL,
                headers=headers,
                files={"images[]": (image_path.name, f, mime)},
                data={"title": image_path.name},
                timeout=TIMEOUT,
            )
        if resp.status_code in (401, 403, 429):
            raise UploadsBlocked(_api_error(resp), resp.status_code)
        if not resp.ok:
            raise UploadError(_api_error(resp))
        post_id = resp.json()["data"]["id"]

        info = requests.get(f"{API_URL}/{post_id}", headers=headers, timeout=TIMEOUT)
        if not info.ok:
            raise UploadError(_api_error(info))
        images = info.json()["data"]["images"]
    except (requests.RequestException, KeyError, ValueError) as e:
        raise UploadError(str(e)) from e
    if not images:
        raise UploadError("no images returned in response")
    return images[0]["link"]


class Uploader:
    """Uploads for one run, with failover between API keys and accounts.

    A rejected key (401) is dropped; a refused account (403, usually its storage
    quota) drops all of that account's keys; the next one takes over and the file
    is retried. A rate limit (429) covers the whole connection, so it never
    switches accounts: uploads stop for the run, and later calls fail at once
    instead of sending every file.
    """

    def __init__(self, upload=upload_image, keys: Optional[List[ApiKey]] = None, accounts=None):
        self.upload = upload
        self._keys = keys
        self._only = accounts
        self.retired: Dict[str, str] = {}
        self.blocked: Optional[str] = None
        self.uploaded = 0
        self.account: Optional[str] = None  # account of the last successful upload
        self.per_account: Dict[str, int] = {}

    @property
    def keys(self) -> List[ApiKey]:
        if self._keys is None:
            _load_dotenv()
            self._keys = load_keys(only=self._only)
        return self._keys

    def _current(self) -> Optional[ApiKey]:
        return next((k for k in self.keys if k.var not in self.retired), None)

    def _block(self, reason: str):
        self.blocked = reason
        logger.error(
            f"imgchest refused the upload ({reason}); not uploading anything else this run"
        )
        raise UploadsBlocked(reason)

    def __call__(self, path: Path) -> str:
        if self.blocked:
            raise UploadError(f"uploads stopped earlier in this run: {self.blocked}")
        try:
            keys = self.keys
        except UploadError as e:
            self._block(str(e))
        if not keys:
            self._block(f"{KEY_PREFIX} is not set (environment or .env)")
        while True:
            key = self._current()
            if key is None:
                self._block(
                    "every API key was refused: "
                    + "; ".join(f"{v}: {r}" for v, r in self.retired.items())
                )
            try:
                link = self.upload(path, key.token)
            except UploadsBlocked as e:
                if e.status not in (401, 403):
                    self._block(str(e))
                gone = (
                    [k for k in self.keys if k.account == key.account] if e.status == 403 else [key]
                )
                for k in gone:
                    self.retired.setdefault(k.var, str(e))
                nxt = self._current()
                logger.warning(
                    f"imgchest refused {key.var} (account '{key.account}'): {e}; "
                    + (
                        f"switching to {nxt.var} (account '{nxt.account}')"
                        if nxt
                        else "no keys left"
                    )
                )
                continue
            self.uploaded += 1
            self.account = key.account
            self.per_account[key.account] = self.per_account.get(key.account, 0) + 1
            return link


# --- database helpers (all SQL for the link cache lives here) ------------------
def _table(table_name):
    from psycopg2 import sql

    return sql.Identifier(table_name)


ADDED_COLUMNS = [
    ("uploaded_at", "TIMESTAMPTZ NOT NULL DEFAULT NOW()"),
    ("account", "TEXT"),  # imgchest account (or "catbox", from imguploader) holding the file
]


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
        # Older tables lack these columns. ALTER TABLE locks the whole table even with
        # IF NOT EXISTS (and deadlocks against a running imguploader), so only run it when needed.
        cur.execute(
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_schema = current_schema() AND table_name = %s",
            (table_name,),
        )
        have = {row[0] for row in cur.fetchall()}
        for column, kind in ADDED_COLUMNS:
            if column not in have:
                cur.execute(
                    sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} " + kind).format(
                        _table(table_name), sql.Identifier(column)
                    )
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


def save_link(conn, table_name, hash_val, link, filename, keep_existing_link=True, account=None):
    """Insert a link; an existing row keeps its link and account (unless told
    otherwise) and only gets a filename if it had none."""
    from psycopg2 import sql

    side = "{t}" if keep_existing_link else "EXCLUDED"
    query = sql.SQL(
        """INSERT INTO {t} (hash, link, filename, account) VALUES (%s, %s, %s, %s)
           ON CONFLICT (hash) DO UPDATE SET
               link = """
        + side
        + """.link,
               account = """
        + side
        + """.account,
               filename = COALESCE({t}.filename, EXCLUDED.filename)"""
    ).format(t=_table(table_name))
    with conn.cursor() as cur:
        cur.execute(query, (hash_val, link, filename, account))


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
    uploader=None,
) -> List[MediaItem]:
    """Resolve every file to a hosted link, in the order given.

    Order of preference: sidecar link (with --sidecar), cached link (by MD5),
    fresh upload (unless --useSaved). Files that end up without a link are
    left out and written to ``skipped_log_file``. Each upload is committed
    straight away, so a later failure never loses links that were uploaded.
    Database errors roll back and propagate to the caller.
    """
    uploader = uploader or Uploader()
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
                save_link(
                    conn,
                    table_name,
                    hash_val,
                    link,
                    path.name,
                    account=getattr(uploader, "account", None),
                )
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
