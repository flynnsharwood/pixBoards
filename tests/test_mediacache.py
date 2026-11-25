import os

import pixBoards.mediacache as mc
from pixBoards.mediacache import MediaCache, compute_md5


def test_hashes_are_cached_until_the_file_changes(tmp_path, make_image, monkeypatch):
    img = make_image(tmp_path / "a.jpg")
    calls = []
    real = mc.compute_md5
    monkeypatch.setattr(mc, "compute_md5", lambda p: calls.append(p) or real(p))

    db = tmp_path / "c.sqlite3"
    with MediaCache(db) as cache:
        first = cache.hashes([img])
    with MediaCache(db) as cache:  # new process, same cache file
        assert cache.hashes([img]) == first
    assert len(calls) == 1
    assert first[img] == compute_md5(img)

    make_image(img, size=(41, 30))  # rewrite: size/mtime change
    os.utime(img, (5, 5))
    with MediaCache(db) as cache:
        assert cache.hashes([img])[img] == compute_md5(img)
    assert len(calls) == 2


def test_info_sizes_timestamps_and_unreadable_files(tmp_path, make_image, cache):
    img = make_image(tmp_path / "a.png", size=(64, 32), mtime=1234)
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not really a video")
    os.utime(video, (99, 99))
    info = cache.info([img, video, tmp_path / "missing.jpg"])
    assert info[img] == (64, 32, 1234)
    assert info[video] == (None, None, 99)
    assert tmp_path / "missing.jpg" not in info


def test_info_and_hash_share_rows(tmp_path, make_image, cache):
    img = make_image(tmp_path / "a.png")
    cache.info([img])
    cache.hashes([img])
    w, h, _ = cache.info([img])[img]  # still there after hashing wrote the row
    assert (w, h) == (40, 30)
