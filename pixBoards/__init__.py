import os

# Single source of truth for the version (read by pyproject.toml).
__version__ = "1.0.1"

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
