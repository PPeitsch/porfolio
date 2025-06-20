#!/usr/bin/env python
import subprocess
import sys


def run_command(command: list[str]) -> str:
    """Runs a shell command and returns its stdout."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout.strip()
    except FileNotFoundError:
        print(
            f"Error: Command '{command[0]}' not found. "
            "Is Git installed and in your PATH?",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}", file=sys.stderr)
        print(f"Stderr: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def get_latest_tag() -> str:
    """Fetches the most recent Git tag from the repository."""
    # git describe --tags --abbrev=0 finds the latest tag pointing to a commit
    return run_command(["git", "describe", "--tags", "--abbrev=0"])


def get_commits_since_tag(tag: str) -> list[str]:
    """Fetches commit messages since the given tag."""
    # git log <tag>..HEAD formats each commit as: <short_hash>--<subject>
    log_format = "--pretty=format:%h--%s"
    commits_str = run_command(["git", "log", f"{tag}..HEAD", log_format])
    if not commits_str:
        return []
    return commits_str.split("\n")


def main():
    """Main function to generate the changelog draft."""
    print("🤖 Starting changelog generator...")
    try:
        latest_tag = get_latest_tag()
        print(f"✅ Found latest tag: {latest_tag}")
    except SystemExit:
        print(
            "Could not determine the latest tag. Is this a git repository with tags?",
            file=sys.stderr,
        )
        sys.exit(1)

    commits = get_commits_since_tag(latest_tag)

    if not commits:
        print("✅ No new commits found since the last tag. Nothing to generate.")
        sys.exit(0)

    print(f"✅ Found {len(commits)} commits since {latest_tag}:")
    for commit in commits:
        print(f"  - {commit}")

    # The logic for parsing and formatting will be added in the next steps.


if __name__ == "__main__":
    main()
