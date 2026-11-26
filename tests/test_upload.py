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

    def save(conn, name, h, link, filename, keep_existing_link=True, account=None):
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

    def refusing(p, token):
        sent.append(p.name)
        raise ic.UploadsBlocked("403 You've used 36.8 GB of your 10 GB storage.", 403)

    uploader = ic.Uploader(refusing, keys=[ic.ApiKey("default", "IMG_CHEST_API_KEY", "k")])
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


def test_rate_limit_blocks_uploads(tmp_path, monkeypatch):
    import requests

    class Resp:
        status_code, reason, ok = 429, "Too Many Requests", False

        def json(self):
            return {"error": "You can only upload 0 more files this hour."}

    monkeypatch.setenv("IMG_CHEST_API_KEY", "x")
    monkeypatch.setattr(requests, "post", lambda *a, **k: Resp())
    img = tmp_path / "a.jpg"
    img.write_bytes(b"a")
    with pytest.raises(ic.UploadsBlocked, match="429"):
        ic.upload_image(img, "x")


KEYS_ENV = {
    "IMG_CHEST_API_KEY": "d0",
    "IMG_CHEST_API_KEY_2": "d2",
    "IMG_CHEST_API_KEY_MAIN_1": "m1",
    "IMG_CHEST_API_KEY_MAIN_2": "m2",
    "IMG_CHEST_API_KEY_ALT": "a",
    "IMG_CHEST_API_KEY_BLANK": " ",
}


def test_load_keys():
    assert [(k.account, k.token) for k in ic.load_keys(KEYS_ENV)] == [
        ("default", "d0"),
        ("default", "d2"),
        ("alt", "a"),
        ("main", "m1"),
        ("main", "m2"),
    ]
    env = {**KEYS_ENV, "IMG_CHEST_ACCOUNTS": "main"}
    assert [k.token for k in ic.load_keys(env)][:2] == ["m1", "m2"]
    assert [k.token for k in ic.load_keys(KEYS_ENV, only=["alt", "main"])] == ["a", "m1", "m2"]
    with pytest.raises(UploadError, match="nope"):
        ic.load_keys(KEYS_ENV, only=["nope"])


def test_uploader_fails_over_between_keys_and_accounts(tmp_path):
    img = tmp_path / "a.jpg"
    img.write_bytes(b"a")
    refused = {"m1": 401, "a": 403}
    sent = []

    def upload(path, token):
        sent.append(token)
        if token in refused:
            raise ic.UploadsBlocked(f"{refused[token]} no", refused[token])
        return f"http://{token}"

    keys = ic.load_keys(KEYS_ENV, only=["main", "alt"])
    up = ic.Uploader(upload, keys=keys)
    assert up(img) == "http://m2" and up.account == "main"  # bad key: next key, same account
    assert sent == ["m1", "m2"]

    keys = ic.load_keys(KEYS_ENV, only=["alt", "default"])
    up = ic.Uploader(upload, keys=keys)
    assert up(img) == "http://d0" and up.account == "default"  # account refused: next account
    assert up.per_account == {"default": 1}


def test_uploader_rate_limit_does_not_switch(tmp_path):
    img = tmp_path / "a.jpg"
    img.write_bytes(b"a")
    sent = []

    def upload(path, token):
        sent.append(token)
        raise ic.UploadsBlocked("429 Upload limit reached", 429)

    up = ic.Uploader(upload, keys=ic.load_keys(KEYS_ENV))
    with pytest.raises(ic.UploadsBlocked):
        up(img)
    with pytest.raises(UploadError, match="stopped earlier"):
        up(img)
    assert sent == ["d0"] and not up.retired


def test_uploader_without_keys(tmp_path, monkeypatch):
    up = ic.Uploader(lambda p, t: "x", keys=[])
    with pytest.raises(ic.UploadsBlocked, match="IMG_CHEST_API_KEY is not set"):
        up(tmp_path / "a.jpg")
