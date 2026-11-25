import os
from pathlib import Path

import pytest

from pixBoards import TEMPLATES_DIR
from pixBoards.arguments import parse_args
from pixBoards.config_loader import ConfigError, build_config, make_config

REPO = Path(__file__).resolve().parent.parent


def config_for(path, *argv):
    return build_config(parse_args(["--config", str(path), *argv]))


def test_example_config_matches_template():
    template = Path(TEMPLATES_DIR, "configTemplate.yml").read_text(encoding="utf-8")
    assert (REPO / "config_example.yml").read_text(encoding="utf-8") == template


def test_template_config_loads(tmp_path):
    p = tmp_path / "boards.yml"
    p.write_text(Path(TEMPLATES_DIR, "configTemplate.yml").read_text(encoding="utf-8"))
    cfg = config_for(p)
    assert cfg["default_layout"] == "masonry"
    assert not cfg["outputDir"].startswith("~")


def test_defaults_and_derived_dirs(write_config):
    p = write_config("masterDir: /data/out/main\ndirectories: [~/pics]\n", name="mine.yml")
    cfg = config_for(p)
    assert cfg["outputDir"] == os.path.join("/data/out", "mine")
    assert cfg["row_height"] == 240 and cfg["lazy_loading"] is True
    assert cfg["directories"] == [os.path.expanduser("~/pics")]
    assert config_for(p, "--upload")["outputDir"] == os.path.join("/data/out", "mine_upload")
    assert config_for(p, "--dir", "/x/holiday/")["outputDir"] == os.path.join(
        "/data/out", "holiday"
    )


def test_cli_overrides_and_old_key_names(write_config):
    p = write_config("masterDir: /o/m\nheight: 300\nlazy-loading: false\ncol_count: 3\n")
    cfg = config_for(p)
    assert cfg["row_height"] == 300 and cfg["lazy_loading"] is False and cfg["col_count"] == 3
    cfg = config_for(p, "--height", "180", "--col", "7", "--pageSize", "10")
    assert (cfg["row_height"], cfg["col_count"], cfg["page_size"]) == (180, 7, 10)


@pytest.mark.parametrize(
    "text, message",
    [
        ("", "empty"),
        ("- just\n- a list\n", "not a mapping"),
        ("directories: []\n", "masterDir"),
        ("masterDir: /o\ndefault_layout: grid\n", "default_layout"),
        ("masterDir: [unclosed\n", "could not read"),
    ],
)
def test_bad_configs(write_config, text, message):
    with pytest.raises(ConfigError, match=message):
        config_for(write_config(text))


def test_missing_config(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        config_for(tmp_path / "nope.yml")


def test_make_config_never_overwrites(tmp_path):
    target = tmp_path / "config.yml"
    assert make_config(target) is True
    target.write_text("mine")
    assert make_config(target) is False
    assert target.read_text() == "mine"
