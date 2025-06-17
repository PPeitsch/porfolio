"""Extracts release notes for a specific version from a CHANGELOG.md file."""

import re
import sys
from typing import Optional


def get_version_section(content: str, version_number: str) -> Optional[str]:
    """
    Find and return the content for a specific version section in the changelog.

    Args:
        content: The full content of the changelog file.
        version_number: The version string to look for (e.g., "1.0.0").

    Returns:
        The content of the version section if found, otherwise None.
    """
    # Regex to find the start of the version section: "## [version]"
    # It captures everything until the next "## [" (start of another version)
    # or the end of the string (\Z).
    # re.escape is used for version_number to handle dots or other special chars.
    escaped_version_number = re.escape(version_number)
    pattern = re.compile(
        r"##\s*\[" + escaped_version_number + r"\][^\n]*\n(.*?)(?=\n##\s*\[|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return None


def main(version_number: str, changelog_filepath: str, output_filepath: str) -> None:
    """
    Read a changelog, extract notes for a version, and write them to an output file.

    Args:
        version_number: The version to extract notes for (e.g., "1.0.0").
        changelog_filepath: Path to the CHANGELOG.md file.
        output_filepath: Path where the extracted notes will be written.
    """
    try:
        with open(changelog_filepath, "r", encoding="utf-8") as f_changelog:
            changelog_content = f_changelog.read()
    except FileNotFoundError:
        print(f"Error: Changelog file not found at '{changelog_filepath}'.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading changelog file '{changelog_filepath}': {e}")
        sys.exit(1)

    extracted_notes = get_version_section(changelog_content, version_number)

    if extracted_notes:
        try:
            with open(output_filepath, "w", encoding="utf-8") as f_output:
                f_output.write(extracted_notes)
            print(
                f"Successfully extracted release notes for version {version_number} "
                f"to '{output_filepath}'."
            )
        except Exception as e:
            print(f"Error writing extracted notes to '{output_filepath}': {e}")
            sys.exit(1)
    else:
        print(
            f"Warning: Version section for '{version_number}' not found in "
            f"'{changelog_filepath}'. Output file will contain a placeholder message."
        )
        try:
            with open(output_filepath, "w", encoding="utf-8") as f_output:
                # Split the long string into multiple lines inside parentheses
                f_output.write(
                    f"No specific release notes found for version {version_number} "
                    f"in {changelog_filepath}.\nPlease ensure the CHANGELOG.md is "
                    "formatted correctly with a section like:\n"
                    f"## [{version_number}] - YYYY-MM-DD"
                )
        except Exception as e:
            print(f"Error writing placeholder message to '{output_filepath}': {e}")
            # Optionally, exit with error if notes must be found:
            # sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        # Split the long string into multiple lines for readability and linting
        print(
            "Usage: python extract_release_notes.py <version_without_v_prefix> "
            "<changelog_file_path> <output_file_path>"
        )
        print(
            "Example: python extract_release_notes.py 1.0.0 "
            "CHANGELOG.md RELEASE_NOTES.md"
        )
        sys.exit(1)

    # Args: script_name, version, changelog_path, output_path
    script_version_number = sys.argv[1]
    script_changelog_file = sys.argv[2]
    script_output_file = sys.argv[3]

    main(script_version_number, script_changelog_file, script_output_file)
