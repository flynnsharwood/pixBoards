import os
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def make_image():
    """make_image(path, size=(w, h), mtime=None, taken=None) -> Path"""

    def _make(path, size=(40, 30), mtime=None, taken=None):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", size, (120, 40, 200))
        if taken:
            exif = Image.Exif()
            exif.get_ifd(0x8769)[36867] = taken  # DateTimeOriginal
            img.save(path, exif=exif)
        else:
            img.save(path)
        if mtime is not None:
            os.utime(path, (mtime, mtime))
        return path

    return _make


@pytest.fixture
def cache(tmp_path):
    from pixBoards.mediacache import MediaCache

    with MediaCache(tmp_path / "cache.sqlite3", workers=2) as c:
        yield c


@pytest.fixture
def write_config(tmp_path):
    def _write(text, name="config.yml"):
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        return p

    return _write
