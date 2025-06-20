#!/usr/bin/env python
import re
import subprocess
import sys
from collections import OrderedDict

# Map conventional commit types to changelog section headers.
# The order here defines the order in the final changelog.
TYPE_TO_CATEGORY_MAP = OrderedDict(
    [
        ("feat", "Features"),
        ("fix", "Bug Fixes"),
        ("perf", "Performance Improvements"),
        ("refactor", "Code Refactoring"),
        ("docs", "Documentation"),
        ("style", "Style"),
        ("test", "Tests"),
        ("build", "Build System"),
        ("ci", "Continuous Integration"),
        ("chore", "Chores & Others"),
        ("revert", "Reverts"),
    ]
)


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
    return run_command(["git", "describe", "--tags", "--abbrev=0"])


def get_commits_since_tag(tag: str) -> list[str]:
    """Fetches commit messages since the given tag."""
    log_format = "--pretty=format:%h--%s"
    commits_str = run_command(["git", "log", f"{tag}..HEAD", log_format])
    if not commits_str:
        return []
    return commits_str.split("\n")


def parse_and_categorize_commits(
    commits: list[str],
) -> dict[str, list[str]]:
    """Parses commits and groups them by category."""
    commit_regex = re.compile(r"^(?P<type>\w+)(?:\(.*\))?!?: (?P<subject>.*)$")
    categorized_commits: "OrderedDict[str, list[str]]" = OrderedDict(
        (category, []) for category in TYPE_TO_CATEGORY_MAP.values()
    )

    for commit in commits:
        hash_part, subject_part = commit.split("--", 1)
        match = commit_regex.match(subject_part)

        if match:
            commit_type = match.group("type")
            subject = match.group("subject").strip()
            # Capitalize the first letter of the subject for better formatting
            subject = subject[0].upper() + subject[1:]
            category = TYPE_TO_CATEGORY_MAP.get(commit_type, "Chores & Others")
            categorized_commits[category].append(f"- {subject} ({hash_part})")
        else:
            # For non-conventional commits, keep them in a general category
            subject = subject_part.strip()
            subject = subject[0].upper() + subject[1:]
            category = "Chores & Others"
            categorized_commits[category].append(f"- {subject} ({hash_part})")

    return categorized_commits


def generate_markdown_output(categorized_commits: dict[str, list[str]]) -> str:
    """Generates a Markdown formatted string from categorized commits."""
    output_lines = []
    for category, commit_list in categorized_commits.items():
        if commit_list:
            output_lines.append(f"\n### {category}\n")
            output_lines.extend(commit_list)
    return "\n".join(output_lines)


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

    print(f"✅ Found {len(commits)} commits since {latest_tag}.")

    categorized_commits = parse_and_categorize_commits(commits)
    markdown_output = generate_markdown_output(categorized_commits)

    if not markdown_output.strip():
        print("✅ All commits were filtered out. Nothing to generate.")
        sys.exit(0)

    print("\n" + "=" * 80)
    print("📋 CHANGELOG DRAFT (copy from here)".center(80))
    print("=" * 80)
    print(markdown_output.strip())
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
