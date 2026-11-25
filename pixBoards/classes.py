from __future__ import annotations

import logging
import os
from math import ceil
from typing import List, Optional

from pixBoards.media import MediaItem

logger = logging.getLogger(__name__)

NEST_SEPARATOR = "_~"


class Page:
    def __init__(
        self, number: int, total: int, items: List[MediaItem], file_location: str, board: "Board"
    ):
        self.number = number
        self.total = total
        self.items = items
        self.file_location = file_location
        self.board = board


class Board:
    """A named list of media. Nested boards use ``_~`` in their name
    (``parent_~child``); see nest_boards.assign_nested_boards."""

    def __init__(
        self,
        name: str,
        output_dir: str,
        items: Optional[List[MediaItem]] = None,
        dummy: bool = False,
        from_list: bool = False,
    ):
        self.name = name
        self.output_dir = str(output_dir)
        self.items = items if items is not None else []
        self.dummy = dummy  # folder without media of its own: gets a sub-index
        self.from_list = from_list
        self.pages: List[Page] = []
        self.nested_boards: List[Board] = []
        parts = name.split(NEST_SEPARATOR)
        self.clean_name = parts[-1]
        self.parent = NEST_SEPARATOR.join(parts[:-1])

    @property
    def no_of_imgs(self) -> int:
        return len(self.items)

    def page_filename(self, number: int, padding: int) -> str:
        return f"{self.name}_{number:0{padding}}.html"

    def paginate(self, per_page: int, padding: int, paginate: bool = True):
        """Split the items into pages. ``paginate=False`` puts everything on one page."""
        if not paginate:
            per_page = max(1, len(self.items))
        total = ceil(len(self.items) / per_page)
        self.pages = [
            Page(
                number=i + 1,
                total=total,
                items=self.items[i * per_page : (i + 1) * per_page],
                file_location=os.path.join(self.output_dir, self.page_filename(i + 1, padding)),
                board=self,
            )
            for i in range(total)
        ]
        logger.debug(f"Board {self.name}: {len(self.items)} items, {total} page(s)")
        return self

    def first_image(self) -> Optional[MediaItem]:
        """First non-video item of this board or, failing that, of a nested board."""
        for item in self.items:
            if not item.is_video:
                return item
        for child in self.nested_boards:
            found = child.first_image()
            if found:
                return found
        return None
