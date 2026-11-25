"""Media file types and the MediaItem record shared by every board."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic")
VIDEO_MIME_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
}
VIDEO_EXTENSIONS = tuple(VIDEO_MIME_TYPES)
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS

# gallery-dl names Pinterest downloads pinterest_<pinId>[_<n>].<ext>
PINTEREST_FILE = re.compile(r"^pinterest_(\d+)(?:_\d+)?\.[^.]+$")
PINTEREST_PIN_URL = "https://www.pinterest.com/pin/{}/"


def extension(name: str) -> str:
    return os.path.splitext(urlparse(name).path if "://" in name else name)[1].lower()


def is_media(name: str) -> bool:
    return extension(name) in MEDIA_EXTENSIONS


@dataclass
class MediaItem:
    """One image or video on a board.

    ``src`` is what the page links to: a ``file://`` URI for local boards, or
    an http(s) link for uploaded and image-list boards. ``path`` is the local
    file when there is one (upload boards keep it, so local metadata such as
    timestamps and sizes still works for them).
    """

    src: str
    path: Optional[Path] = None
    hash: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    timestamp: Optional[float] = None

    @property
    def name(self) -> str:
        if self.path is not None:
            return self.path.name
        return unquote(os.path.basename(urlparse(self.src).path)) or self.src

    @property
    def ext(self) -> str:
        return extension(self.path.name if self.path is not None else self.src)

    @property
    def is_video(self) -> bool:
        return self.ext in VIDEO_EXTENSIONS

    @property
    def mime(self) -> Optional[str]:
        return VIDEO_MIME_TYPES.get(self.ext)

    @property
    def source(self) -> Optional[str]:
        """Link to the original Pinterest pin, detected from the file name."""
        match = PINTEREST_FILE.match(self.name)
        return PINTEREST_PIN_URL.format(match.group(1)) if match else None

    @property
    def aspect(self) -> Optional[float]:
        if self.width and self.height:
            return self.width / self.height
        return None
