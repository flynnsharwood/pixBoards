"""Render boards to HTML with Jinja templates (autoescaped)."""

from __future__ import annotations

import logging
import random
import shutil
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pixBoards import TEMPLATES_DIR, __version__
from pixBoards.classes import NEST_SEPARATOR, Board, Page

logger = logging.getLogger(__name__)

ENV = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
PAGE_WINDOW = 5  # page links shown on each side of the current page
STATIC_FILES = {
    "template.css": "styles.css",
    "template.js": "script.js",
    "favicon.png": "favicon.png",
}


def breadcrumb(board_name: str, padding: int):
    """[(label, href or None), ...] from the index down to ``board_name``."""
    crumbs = [("index", "index.html")]
    parts = board_name.split(NEST_SEPARATOR) if board_name else []
    for i, part in enumerate(parts):
        href = None
        if i < len(parts) - 1:
            href = f"{NEST_SEPARATOR.join(parts[: i + 1])}_{1:0{padding}}.html"
        crumbs.append((part, href))
    return crumbs


def pagination(page: Page, padding: int):
    if page.total <= 1:
        return None
    board = page.board

    def href(n):
        return board.page_filename(n, padding)

    start = max(1, page.number - PAGE_WINDOW)
    end = min(page.total, page.number + PAGE_WINDOW)
    return {
        "current": page.number,
        "total": page.total,
        "pages": [(n, href(n)) for n in range(start, end + 1)],
        "first": href(1) if start > 1 else None,
        "last": href(page.total) if end < page.total else None,
        "prev": href(page.number - 1) if page.number > 1 else None,
        "next": href(page.number + 1) if page.number < page.total else None,
        "prefix": f"{board.name}_",
        "padding": padding,
    }


def _item(item):
    ar = item.aspect
    return {
        "src": item.src,
        "name": item.name,
        "copy_text": item.hash or item.src,
        "is_video": item.is_video,
        "mime": item.mime,
        "ar": f"{ar:.4f}" if ar else None,
    }


def _settings(config):
    return {
        "layout": config["default_layout"],
        "cols": config["col_count"],
        "row_height": config["row_height"],
        "margin": config["margin"],
        "lazy": config["lazy_loading"],
    }


def render_page(page: Page, config, timestamp: str) -> str:
    padding = config["padding"]
    images = [i for i in page.items if not i.is_video]
    return ENV.get_template("template.html").render(
        title=f"{page.board.clean_name}, Page {page.number} of {page.total}",
        heading=page.board.clean_name,
        breadcrumb=breadcrumb(page.board.name, padding),
        items=[_item(i) for i in page.items],
        page_count=len(page.items),
        board_count=page.board.no_of_imgs,
        pagination=pagination(page, padding),
        background=random.choice(images).src if images else None,
        settings=_settings(config),
        version=__version__,
        timestamp=timestamp,
    )


def _tree(boards, padding):
    """Nested dicts for the index template, biggest boards first."""
    nodes = []
    for b in sorted(boards, key=lambda x: x.no_of_imgs, reverse=True):
        thumb = b.first_image()
        nodes.append(
            {
                "name": b.clean_name,
                "href": b.page_filename(1, padding),
                "count": b.no_of_imgs,
                "thumb": thumb.src if thumb else None,
                "children": _tree(b.nested_boards, padding),
            }
        )
    return nodes


def render_index(boards, config, timestamp: str, board: Board = None) -> str:
    """The root index (``board=None``) or the sub-index of a folder board."""
    padding = config["padding"]
    return ENV.get_template("index_template.html").render(
        title=board.clean_name if board else "Index",
        breadcrumb=breadcrumb(board.name if board else "", padding),
        tree=_tree(boards, padding),
        settings=_settings(config),
        version=__version__,
        timestamp=timestamp,
    )


def write_output(root_boards, boards, config):
    out = Path(config["outputDir"])
    out.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for b in boards:
        for p in b.pages:
            Path(p.file_location).write_text(render_page(p, config, timestamp), encoding="utf-8")
            logger.debug(f"wrote {p.file_location}")

    (out / "index.html").write_text(render_index(root_boards, config, timestamp), encoding="utf-8")
    for b in boards:
        if b.dummy:
            sub = out / b.page_filename(1, config["padding"])
            sub.write_text(
                render_index(b.nested_boards, config, timestamp, board=b), encoding="utf-8"
            )

    for src, dest in STATIC_FILES.items():
        shutil.copyfile(Path(TEMPLATES_DIR) / src, out / dest)
