from pixBoards.cli import main


def test_full_run(tmp_path, make_image, monkeypatch):
    for i in range(5):
        make_image(tmp_path / "pics" / f"img{i}.jpg", mtime=1000 + i)
    make_image(tmp_path / "pics" / "sub" / "deep.png", mtime=1)
    (tmp_path / "pics" / "nothing").mkdir()
    out = tmp_path / "out" / "boards"
    (tmp_path / "config.yml").write_text(
        f"masterDir: {out}\n"
        f"directories: [{tmp_path / 'pics'}]\n"
        f"page_size: 2\n"
        f"cache_file: {tmp_path / 'cache.sqlite3'}\n"
        f"json_dump: true\n"
    )
    monkeypatch.chdir(tmp_path)

    assert main(["--recent", "3", "--random", "-1"]) == 0
    files = {p.name for p in out.iterdir()}
    assert {"index.html", "styles.css", "script.js", "favicon.png", "dump.json"} <= files
    assert {
        "pics_001.html",
        "pics_003.html",
        "pics_~sub_001.html",
        "pics_~nothing_001.html",
    } <= files
    assert (
        "recent imgs_002.html" in files and "recent imgs_003.html" not in files
    )  # 3 items, 2/page
    assert (tmp_path / "logs").is_dir()

    recent = (out / "recent imgs_001.html").read_text()
    assert recent.index("img4.jpg") < recent.index("img3.jpg")  # newest first


def test_exit_codes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main([]) == 1  # no config.yml
    assert main(["--makeConfig"]) == 0
    assert main(["--makeConfig"]) == 1  # already exists
    assert (tmp_path / "config.yml").exists()
