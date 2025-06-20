#!/usr/bin/env python
"""Generate a changelog based on git history.

This script examines the git history since the last tag and
generates a formatted changelog based on commit messages, categorizing
them by conventional commit types.
"""

import re
import subprocess  # nosec B404
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def get_latest_tag() -> Optional[str]:
    """Retrieve the most recent tag from the git repository."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],  # nosec B603, B607
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        try:
            result = subprocess.run(
                ["git", "rev-list", "--max-parents=0", "HEAD"],  # nosec B603, B607
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()  # Fallback to initial commit if no tags
        except subprocess.CalledProcessError:
            return None  # Should not happen in a valid git repo


def get_current_tag() -> Optional[str]:
    """Retrieve the tag associated with the current commit, if any."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],  # nosec B603, B607
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_commit_history(since_tag: str) -> List[str]:
    """Retrieve the commit history since a specified tag, separated by null chars."""
    # Format: subject, body, hash, author, date, separated by tabs.
    # Commits are separated by a null character (%x00) for robust parsing.
    commit_format = "--pretty=format:%s%x09%b%x09%h%x09%an%x09%ad%x00"
    command = ["git", "log", commit_format, "--date=short"]
    if since_tag:
        if not (len(since_tag) == 40 and re.match(r"^[0-9a-f]{40}$", since_tag)):
            command.insert(2, f"{since_tag}..HEAD")

    result = subprocess.run(
        command,  # nosec B603
        capture_output=True,
        text=True,
        check=True,
    )
    # Split by the null character to get a list of commits
    return result.stdout.strip().split("\x00")


def categorize_commits(
    commits: List[str],
) -> Dict[str, List[Tuple[str, str, str, str, str]]]:
    """Categorize commits by their conventional commit type."""
    categories: Dict[str, List[Tuple[str, str, str, str, str]]] = {
        "Features": [],
        "Bug Fixes": [],
        "Documentation": [],
        "Performance": [],
        "Refactoring": [],
        "Style": [],
        "Testing": [],
        "Build": [],
        "CI": [],
        "Chore": [],
        "Other": [],
    }
    type_mapping = {
        "feat": "Features",
        "fix": "Bug Fixes",
        "docs": "Documentation",
        "style": "Style",
        "refactor": "Refactoring",
        "perf": "Performance",
        "test": "Testing",
        "build": "Build",
        "ci": "CI",
        "chore": "Chore",
    }
    pattern = r"^([a-z]+)(\([a-zA-Z0-9_ -]+\))?(!?):\s*(.*)"

    for commit_line in commits:
        if not commit_line.strip():
            continue
        try:
            subject, body, commit_hash, author, date_str = commit_line.split("\t", 4)
            subject = subject.strip()
            body = body.strip()

            match = re.match(pattern, subject)
            commit_type = "other"
            is_breaking = False

            if match:
                commit_type = match.group(1).lower()
                is_breaking = match.group(3) == "!"

            if "BREAKING CHANGE" in body:
                is_breaking = True

            category_key = type_mapping.get(commit_type, "Other")
            if is_breaking and category_key not in ["Features", "Bug Fixes"]:
                category_key = "Bug Fixes"

            # Always use the full subject line for the description.
            categories[category_key].append(
                (subject, body, commit_hash, author, date_str)
            )
        except ValueError:
            categories["Other"].append((commit_line, "", "", "", ""))
            continue
    return categories


def format_changelog(
    categories: Dict[str, List[Tuple[str, str, str, str, str]]],
    current_tag: Optional[str],
) -> str:
    """Format the categorized commits into a changelog string."""
    now_date = datetime.now().strftime("%Y-%m-%d")
    header = (
        f"## [{current_tag.lstrip('v')}] - {now_date}\n"
        if current_tag
        else f"## [Unreleased] - {now_date}\n"
    )

    content_parts: List[str] = [header]
    ordered_categories = [
        "Features",
        "Bug Fixes",
        "Performance",
        "Refactoring",
        "Testing",
        "Documentation",
        "Style",
        "Build",
        "CI",
        "Chore",
        "Other",
    ]

    found_commits = False
    for category_key in ordered_categories:
        commits_in_category = categories.get(category_key, [])
        if commits_in_category:
            found_commits = True
            content_parts.append(f"### {category_key}\n")
            for subject, body, commit_hash, author, date_str in commits_in_category:
                short_hash = commit_hash[:7] if commit_hash else ""
                content_parts.append(f"- {subject} ({short_hash})")
                if body:
                    indented_body = "\n".join(
                        f"  {line}" for line in body.strip().split("\n")
                    )
                    content_parts.append(f"\n{indented_body}\n")
            content_parts.append("")

    if not found_commits:
        content_parts.append("No significant changes since the last release.\n")

    return "\n".join(content_parts).strip()


def main():
    """Generate and print the changelog based on git history."""
    latest_tagged_commit = get_latest_tag()
    current_release_tag = get_current_tag()

    if latest_tagged_commit:
        commits_list = get_commit_history(latest_tagged_commit)
        if not commits_list and current_release_tag:
            print(format_changelog({}, current_release_tag))
            return

        categorized = categorize_commits(commits_list)
        changelog_output = format_changelog(categorized, current_release_tag)
        print(changelog_output)
    else:
        print("## [Initial Release]\n\n- First version of the project.\n")


if __name__ == "__main__":
    main()
