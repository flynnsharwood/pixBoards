"""process_images against an in-memory stand-in for the link cache table."""

import pytest

import pixBoards.imgchest as ic
from pixBoards.imgchest import UploadError, process_images


class FakeConn:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


@pytest.fixture
def db(monkeypatch):
    """Replace the SQL helpers with a dict: hash -> link."""
    table = {}

    def lookup(conn, name, hashes):
        return {h: table[h] for h in hashes if h in table}

    def save(conn, name, h, link, filename, keep_existing_link=True):
        table.setdefault(h, link)

    monkeypatch.setattr(ic, "lookup_links", lookup)
    monkeypatch.setattr(ic, "save_link", save)
    monkeypatch.setattr(ic, "backfill_filenames", lambda *a: None)
    return table


def run(paths, cache, tmp_path, **kw):
    return process_images(
        paths, FakeConn(), "t", cache, skipped_log_file=str(tmp_path / "skipped.log"), **kw
    )


def test_links_stay_aligned_with_files(tmp_path, make_image, cache, db):
    paths = [make_image(tmp_path / f"{n}.jpg", size=(10 + i, 10)) for i, n in enumerate("cab")]
    hashes = cache.hashes(paths)
    db[hashes[paths[1]]] = "http://cached/a"  # middle one already uploaded

    uploaded = []

    def fake_upload(p):
        uploaded.append(p.name)
        if p.name == "b.jpg":
            raise UploadError("boom")
        return f"http://new/{p.name}"

    items = run(paths, cache, tmp_path, uploader=fake_upload)
    assert [(i.path.name, i.src) for i in items] == [
        ("c.jpg", "http://new/c.jpg"),
        ("a.jpg", "http://cached/a"),
    ]
    assert all(i.hash == hashes[i.path] for i in items)
    assert uploaded == ["c.jpg", "b.jpg"]
    assert "b.jpg -> upload failed: boom" in (tmp_path / "skipped.log").read_text()
    assert db[hashes[paths[0]]] == "http://new/c.jpg"  # saved straight away


def test_use_saved_never_uploads(tmp_path, make_image, cache, db):
    p = make_image(tmp_path / "x.jpg")

    def no_upload(_):
        raise AssertionError("should not upload")

    assert run([p], cache, tmp_path, use_saved=True, uploader=no_upload) == []
    assert "--useSaved" in (tmp_path / "skipped.log").read_text()


def test_sidecar_link_wins(tmp_path, make_image, cache, db):
    p = make_image(tmp_path / "x.jpg")
    (tmp_path / "x.jpg.txt").write_text("https://side/car.jpg\n")
    items = run([p], cache, tmp_path, use_sidecar=True, uploader=lambda _: "http://new")
    assert items[0].src == "https://side/car.jpg"


def test_db_error_rolls_back_and_propagates(tmp_path, make_image, cache, monkeypatch):
    p = make_image(tmp_path / "x.jpg")

    def broken(*a):
        raise RuntimeError("db down")

    monkeypatch.setattr(ic, "lookup_links", broken)
    conn = FakeConn()
    with pytest.raises(RuntimeError):
        process_images([p], conn, "t", cache)
    assert conn.rollbacks == 1


def test_sidecar_parsing(tmp_path):
    img = tmp_path / "a.png"
    assert ic.sidecar_link(img) is None
    (tmp_path / "a.png.txt").write_text("not a link\n")
    assert ic.sidecar_link(img) is None
    (tmp_path / "a.png.txt").write_text("  http://ok/a.png  \nsecond\n")
    assert ic.sidecar_link(img) == "http://ok/a.png"


def test_uploads_stop_after_imgchest_refuses(tmp_path, make_image, cache, db):
    paths = [make_image(tmp_path / f"{i}.jpg", size=(10 + i, 10)) for i in range(4)]
    sent = []

    def refusing(p):
        sent.append(p.name)
        raise ic.UploadsBlocked("403 You've used 36.8 GB of your 10 GB storage.")

    uploader = ic.Uploader(refusing)
    assert run(paths, cache, tmp_path, uploader=uploader) == []
    assert sent == ["0.jpg"]  # nothing else was sent
    assert "10 GB storage" in uploader.blocked
    log = (tmp_path / "skipped.log").read_text()
    assert log.count("uploads stopped earlier in this run") == 3


def test_api_error_message():
    class Resp:
        status_code, reason = 403, "Forbidden"

        def __init__(self, body):
            self.body = body

        def json(self):
            if self.body is None:
                raise ValueError
            return self.body

    assert ic._api_error(Resp({"error": "quota"})) == "403 quota"
    assert ic._api_error(Resp({"message": "nope"})) == "403 nope"
    assert ic._api_error(Resp(None)) == "403 Forbidden"
