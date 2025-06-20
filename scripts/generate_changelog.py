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
    """Retrieve the commit history since a specified tag."""
    command = ["git", "log", "--pretty=format:%s|%h|%an|%ad", "--date=short"]
    if since_tag:  # Only add range if since_tag is not an initial commit hash
        # if since_tag is a full commit hash it might be the initial commit
        if not (len(since_tag) == 40 and re.match(r"^[0-9a-f]{40}$", since_tag)):
            command.insert(2, f"{since_tag}..HEAD")

    result = subprocess.run(
        command,  # nosec B603
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()


def categorize_commits(
    commits: List[str],
) -> Dict[str, List[Tuple[str, str, str, str]]]:
    """Categorize commits by their conventional commit type."""
    categories: Dict[str, List[Tuple[str, str, str, str]]] = {
        "Features": [],
        "Bug Fixes": [],
        "Documentation": [],
        "Performance": [],
        "Refactoring": [],
        "Style": [],
        "Testing": [],
        "Build": [],
        "CI": [],
        "Chore": [],  # Added Chore
        "Other": [],
    }

    type_mapping = {
        "feat": "Features",
        "fix": "Bug Fixes",
        "docs": "Documentation",
        "style": "Style",  # Kept separate from Other for more granularity
        "refactor": "Refactoring",
        "perf": "Performance",
        "test": "Testing",
        "build": "Build",
        "ci": "CI",
        "chore": "Chore",  # Added Chore
    }

    pattern = r"^([a-z]+)(\([a-zA-Z0-9_ -]+\))?:\s*(.*)"
    # Example: feat(parser): add ability to parse arrays
    # Group 1: type (feat)
    # Group 2: scope ((parser)) - optional
    # Group 3: description (add ability to parse arrays)

    for commit_line in commits:
        try:
            message, commit_hash, author, date_str = commit_line.split("|", 3)
            message = message.strip()

            match = re.match(pattern, message)
            commit_type = "other"  # Default if no conventional prefix
            description = message  # Default if no conventional prefix

            if match:
                commit_type = match.group(1).lower()
                # scope = match.group(2) # Scope can be captured if needed
                description = match.group(3).strip()

            category_key = type_mapping.get(commit_type, "Other")
            categories[category_key].append(
                (description, commit_hash, author, date_str)
            )
        except ValueError:
            # Fallback for commits not matching the split pattern
            categories["Other"].append(
                (commit_line, "", "", "")
            )  # Store raw line if split fails
            continue
    return categories


def format_changelog(
    categories: Dict[str, List[Tuple[str, str, str, str]]], current_tag: Optional[str]
) -> str:
    """Format the categorized commits into a changelog string."""
    now_date = datetime.now().strftime("%Y-%m-%d")

    if current_tag:
        header = f"## [{current_tag.lstrip('v')}] - {now_date}\n\n"
    else:
        header = f"## [Unreleased] - {now_date}\n\n"

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
            for description, commit_hash, author, date_str in commits_in_category:
                # Limit hash to 7 characters for brevity
                short_hash = commit_hash[:7] if commit_hash else ""
                content_parts.append(f"- {description} ({short_hash})")
            content_parts.append("\n")

    if not found_commits:
        content_parts.append("No significant changes since the last release.\n")

    return "\n".join(content_parts)


def main():
    """Generate and print the changelog based on git history."""
    latest_tagged_commit = get_latest_tag()
    current_release_tag = get_current_tag()  # This will be the new tag being released

    if latest_tagged_commit:
        commits_list = get_commit_history(latest_tagged_commit)
        if not commits_list and current_release_tag:
            print(format_changelog({}, current_release_tag))
            return

        categorized = categorize_commits(commits_list)
        changelog_output = format_changelog(categorized, current_release_tag)
        print(changelog_output)
    else:
        # This case might occur if there are no tags and get_latest_tag returned None
        print("## [Initial Release]\n\n- First version of the project.\n")


if __name__ == "__main__":
    main()
