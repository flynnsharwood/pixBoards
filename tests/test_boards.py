from pathlib import Path

from pixBoards.boardmakers import (
    _all_items,
    descBoard,
    randomBoard,
    reddit_sort_key,
    scan_directories,
    standardBoards,
)
from pixBoards.classes import Board
from pixBoards.media import MediaItem
from pixBoards.nest_boards import assign_nested_boards


def items(n, prefix="http://x/"):
    return [MediaItem(src=f"{prefix}{i}.jpg") for i in range(n)]


def test_paginate_pages_and_filenames():
    b = Board("a_~b", "/out", items(5)).paginate(per_page=2, padding=3)
    assert [len(p.items) for p in b.pages] == [2, 2, 1]
    assert [p.number for p in b.pages] == [1, 2, 3]
    assert all(p.total == 3 for p in b.pages)
    assert b.pages[0].file_location == str(Path("/out") / "a_~b_001.html")
    assert b.pages[2].board is b


def test_paginate_disabled_and_empty():
    assert len(Board("a", "/o", items(7)).paginate(2, 3, paginate=False).pages) == 1
    assert Board("a", "/o", []).paginate(2, 3).pages == []


def test_board_names():
    b = Board("root_~child_~leaf", "/o")
    assert b.clean_name == "leaf"
    assert b.parent == "root_~child"


def test_assign_nested_boards_uses_closest_existing_ancestor():
    names = ["r", "r_~a", "r_~a_~b", "r_~x_~y", "other"]
    boards = [Board(n, "/o") for n in names]
    roots = assign_nested_boards(boards)
    by = {b.name: b for b in boards}
    assert [b.name for b in roots] == ["r", "other"]
    assert [c.name for c in by["r"].nested_boards] == ["r_~a", "r_~x_~y"]  # r_~x missing
    assert [c.name for c in by["r_~a"].nested_boards] == ["r_~a_~b"]


def test_first_image_skips_videos_and_descends():
    parent = Board("p", "/o", [MediaItem("http://x/v.mp4")])
    child = Board("p_~c", "/o", [MediaItem("http://x/a.png")])
    parent.nested_boards.append(child)
    assert parent.first_image().src == "http://x/a.png"


def test_scan_directories(tmp_path, make_image):
    make_image(tmp_path / "pics" / "b.jpg")
    make_image(tmp_path / "pics" / "a.png")
    (tmp_path / "pics" / "notes.txt").write_text("x")
    make_image(tmp_path / "pics" / "sub" / "c.jpg")
    (tmp_path / "pics" / "empty").mkdir()

    result = dict(scan_directories([tmp_path / "pics", tmp_path / "missing"]))
    assert set(result) == {"pics", "pics_~empty", "pics_~sub"}
    assert [p.name for p in result["pics"]] == ["a.png", "b.jpg"]
    assert result["pics_~empty"] == []
    assert all(p.is_absolute() for p in result["pics"])


def test_standard_boards_have_uris_sizes_and_dummies(tmp_path, make_image, cache):
    make_image(tmp_path / "pics" / "my pic.jpg", size=(60, 30))
    (tmp_path / "pics" / "empty").mkdir()
    boards = {b.name: b for b in standardBoards([tmp_path / "pics"], "/out", cache)}
    item = boards["pics"].items[0]
    assert item.src.startswith("file://") and item.src.endswith("my%20pic.jpg")
    assert (item.width, item.height) == (60, 30)
    assert item.aspect == 2
    assert boards["pics_~empty"].dummy


def test_all_items_dedupes_by_link():
    a = Board("a", "/o", [MediaItem("http://x/1.jpg"), MediaItem("http://x/2.jpg")])
    b = Board("b", "/o", [MediaItem("http://x/2.jpg"), MediaItem("http://y/2.jpg")])
    assert [i.src for i in _all_items([a, b])] == [
        "http://x/1.jpg",
        "http://x/2.jpg",
        "http://y/2.jpg",
    ]


def test_random_board_counts():
    src = [Board("a", "/o", items(10))]
    assert len(randomBoard(src, 3, "/o").items) == 3
    assert len(randomBoard(src, -1, "/o").items) == 10
    assert len(randomBoard(src, 50, "/o").items) == 10


def test_desc_board_sorts_by_timestamp_and_truncates():
    its = [MediaItem(f"http://x/{i}.jpg", timestamp=t) for i, t in enumerate([5, None, 9, 1])]
    b = descBoard([Board("a", "/o", its)], 2, "/o")
    assert [i.timestamp for i in b.items] == [9, 5]
    everything = descBoard([Board("a", "/o", its)], -1, "/o")
    assert [i.timestamp for i in everything.items] == [9, 5, 1, None]  # unknown last


def test_desc_board_uses_exif_date_over_mtime(tmp_path, make_image, cache):
    # old file time but newer EXIF date (2040) -> first; the rest by mtime (2033, 2001)
    make_image(tmp_path / "pics" / "exif.jpg", mtime=1000, taken="2040:01:01 10:00:00")
    make_image(tmp_path / "pics" / "new.jpg", mtime=2_000_000_000)
    make_image(tmp_path / "pics" / "old.jpg", mtime=1_000_000_000)
    boards = standardBoards([tmp_path / "pics"], "/out", cache)
    order = [i.name for i in descBoard(boards, -1, "/o").items]
    assert order == ["exif.jpg", "new.jpg", "old.jpg"]


def test_reddit_sort_key():
    assert reddit_sort_key(MediaItem("http://x/zz%20title.jpg")) == int("zz", 36)
    assert reddit_sort_key(MediaItem("http://x/abc title.jpg")) == int("abc", 36)
    assert reddit_sort_key(MediaItem("http://x/no-id_here.jpg")) == -1
    its = [MediaItem("http://x/a%20t.jpg"), MediaItem("http://x/zz%20t.jpg")]
    assert descBoard([Board("b", "/o", its)], -1, "/o", reddit=True).items[0].name == "zz t.jpg"


def test_media_item_properties():
    v = MediaItem("http://x/clip.WEBM?x=1")
    assert v.is_video and v.mime == "video/webm"
    assert MediaItem("http://x/a.jpg").mime is None
    assert MediaItem("file:///p/a%20b.jpg", path=Path("/p/a b.jpg")).name == "a b.jpg"


def test_pinterest_source_detection():
    pin = "https://www.pinterest.com/pin/{}/"
    assert MediaItem("file:///x/pinterest_123.jpg", path=Path("/x/pinterest_123.jpg")).source == (
        pin.format(123)
    )
    assert MediaItem("http://h/pinterest_123_456.png").source == pin.format(123)
    assert MediaItem(
        "https://cdn.imgchest.com/files/abc.jpg", path=Path("/p/pinterest_9.mp4")
    ).source == (
        pin.format(9)  # upload boards: detected from the local file, not the link
    )
    for name in ("other.jpg", "pinterest_.jpg", "pinterest_12a.jpg", "my_pinterest_1.jpg"):
        assert MediaItem(f"http://h/{name}").source is None, name
