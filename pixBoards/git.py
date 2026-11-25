import logging
import os
import subprocess

logger = logging.getLogger(__name__)

# Credential helper that reads the username/token from environment variables.
# This keeps the token out of the remote URL, out of .git/config, out of the
# process argument list and out of the console output.
_ENV_CREDENTIAL_HELPER = (
    "!f() { echo username=$PIXBOARDS_GIT_USER; echo password=$PIXBOARDS_GIT_PAT; }; f"
)


def _git(output_dir, *cmd, check=True, **kwargs):
    return subprocess.run(["git", "-C", output_dir, *cmd], check=check, **kwargs)


def git_push_repo(output_dir, remote_url, username, token):
    output_dir = os.path.abspath(output_dir)
    logger.info(f"Pushing {output_dir} to {remote_url}")

    try:
        # Initialize repo if not already initialized
        if not os.path.exists(os.path.join(output_dir, ".git")):
            _git(output_dir, "init")

        # Switch to (or create) the main branch
        result = _git(output_dir, "branch", "--list", "main", capture_output=True, text=True)
        if result.stdout.strip():
            _git(output_dir, "checkout", "main")
        else:
            _git(output_dir, "checkout", "-b", "main")

        _git(output_dir, "add", ".")
        # check=False: "nothing to commit" is not an error here
        _git(output_dir, "commit", "-m", "automated commit", check=False)

        # Point origin at the plain URL. set-url also scrubs any token that
        # older versions of pixBoards embedded in the stored remote URL.
        remotes = _git(output_dir, "remote", capture_output=True, text=True).stdout.split()
        if "origin" in remotes:
            _git(output_dir, "remote", "set-url", "origin", remote_url)
        else:
            _git(output_dir, "remote", "add", "origin", remote_url)

        env = {
            **os.environ,
            "PIXBOARDS_GIT_USER": username,
            "PIXBOARDS_GIT_PAT": token,
            "GIT_TERMINAL_PROMPT": "0",
        }
        subprocess.run(
            [
                "git",
                "-C",
                output_dir,
                # empty value clears any configured helpers, then add ours
                "-c",
                "credential.helper=",
                "-c",
                f"credential.helper={_ENV_CREDENTIAL_HELPER}",
                "push",
                "--set-upstream",
                "origin",
                "main",
            ],
            check=True,
            env=env,
        )
        logger.info("Successfully pushed to remote repository.")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e}")
        return False


def push_output(config):
    """Push the output folder using remote_url / gitUsername from the config
    and the GITHUB_PAT environment variable (or .env file)."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:  # python-dotenv is optional; plain env vars still work
        pass
    token = os.getenv("GITHUB_PAT")
    remote_url = config.get("remote_url")
    username = config.get("gitUsername")

    if not (remote_url and username and token):
        logger.warning(
            "Missing remote_url / gitUsername in config or GITHUB_PAT in the "
            "environment; cannot push."
        )
        return False

    return git_push_repo(config["outputDir"], remote_url, username, token)
