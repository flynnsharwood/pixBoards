import logging
import os

import yaml

from pixBoards import TEMPLATES_DIR

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = "config.yml"
CONFIG_TEMPLATE = os.path.join(TEMPLATES_DIR, "configTemplate.yml")
LAYOUTS = ("masonry", "justified")


class ConfigError(Exception):
    """Raised when the config file is missing or invalid."""


def expand_path(p):
    return os.path.expanduser(os.path.expandvars(str(p)))


def load_config(yml_path):
    try:
        with open(yml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigError(
            f"{yml_path} not found. Use --makeConfig to create a template config."
        ) from None
    except (OSError, yaml.YAMLError) as e:
        raise ConfigError(f"could not read {yml_path}: {e}") from e

    if not isinstance(config, dict):
        raise ConfigError(
            f"{yml_path} is empty or not a mapping. Use --makeConfig to create a template config."
        )
    return config


def make_config(path=DEFAULT_CONFIG_FILE):
    """Write the template config. Never overwrites an existing file."""
    with open(CONFIG_TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()
    try:
        with open(path, "x", encoding="utf-8") as f:
            f.write(template)
    except FileExistsError:
        logger.warning(f"{path} already exists, not overwriting it.")
        return False
    logger.info(f"wrote template config to {path}")
    return True


def _first(config, *keys, default=None):
    for key in keys:
        if config.get(key) is not None:
            return config[key]
    return default


DB_DEFAULTS = {
    "host": "localhost",
    "server_port": 5432,
    "user": "postgres",
    "password": None,
    "dbname": "boards",
    "tableName": "image_cache",
}


def build_config(args):
    """Load the config file and apply command line overrides.

    Adds the derived keys ``masterDir`` and ``outputDir``.
    """
    config_file = args.config or DEFAULT_CONFIG_FILE
    config = load_config(config_file)

    config["col_count"] = args.col or config.get("col_count", 5)
    config["margin"] = args.margin or config.get("margin", 20)
    config["page_size"] = args.pageSize or config.get("page_size", 100000)
    # "height" was the old name of row_height
    config["row_height"] = args.height or _first(config, "row_height", "height", default=240)
    config["lazy_loading"] = bool(_first(config, "lazy_loading", "lazy-loading", default=True))
    config.setdefault("padding", 3)
    config.setdefault("paginate", True)
    config.setdefault("json_dump", False)
    config["source_links"] = bool(config.get("source_links", False))
    # imgchest accounts to upload with, in order (--account overrides the config)
    accounts = getattr(args, "account", None) or config.get("imgchest_accounts") or []
    if isinstance(accounts, str):
        accounts = [accounts]
    config["imgchest_accounts"] = [
        a.strip() for v in accounts for a in str(v).split(",") if a.strip()
    ]
    # database (--upload, --saveBoards); no password means libpq's PGPASSWORD / ~/.pgpass
    for key, value in DB_DEFAULTS.items():
        config.setdefault(key, value)

    layout = str(config.get("default_layout", "masonry")).lower()
    if layout not in LAYOUTS:
        raise ConfigError(f"default_layout must be one of {', '.join(LAYOUTS)}, not {layout!r}")
    config["default_layout"] = layout

    if config.get("cache_file"):
        config["cache_file"] = expand_path(config["cache_file"])
    config["directories"] = [expand_path(d) for d in (config.get("directories") or [])]

    if not config.get("masterDir"):
        raise ConfigError(f"{config_file} has no masterDir set.")

    master_dir = expand_path(config["masterDir"])
    if args.config:
        master_dir = os.path.join(
            os.path.dirname(master_dir),
            os.path.splitext(os.path.basename(config_file))[0],
        )
    if args.dir:
        master_dir = os.path.join(
            os.path.dirname(master_dir), os.path.basename(os.path.normpath(args.dir))
        )

    config["masterDir"] = master_dir
    config["outputDir"] = master_dir + ("_upload" if args.upload else "")
    return config
