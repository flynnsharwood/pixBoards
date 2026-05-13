import os
import subprocess

# this gets the latest git commit hash. i will not be setting the version in the setup.py.
# def get_git_version():
#     try:
#         commit_hash = (
#             subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
#             .decode()
#             .strip()
#         )
#         return commit_hash
#     except Exception:
#         return "untracked"


# __version__ = get_git_version()
<<<<<<< HEAD
__version__ = "0.2.29" 
=======
__version__ = "0.2.30" 
>>>>>>> 3315cef6dca1af6578845ae2ed3c91e934df64b5

templates_folder_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates"
)

with open(os.path.join(templates_folder_path, "configTemplate.yml"), "r") as f:
    configTemplate = f.read()
