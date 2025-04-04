from flask import jsonify, current_app, g
from . import cli_bp
from common.utils import load_cv_data, load_projects_data
import logging
import textwrap

logger = logging.getLogger(__name__)


# --- Helper to get cached data within the context of this blueprint ---
def get_cached_data(data_type="cv"):
    """Helper to load data once per app context for CLI."""
    if data_type == "cv":
        if "cv_data" not in g:
            g.cv_data = load_cv_data()
            logger.info("CLI: CV data loaded into context g")
        return g.cv_data
    elif data_type == "projects":
        if "projects_data" not in g:
            g.projects_data, g.projects_dict = load_projects_data()
            logger.info("CLI: Projects data loaded into context g")

        if "projects_dict" not in g and "projects_data" in g:
            g.projects_dict = (
                {p.get("id", f"proj_{i}"): p for i, p in enumerate(g.projects_data)}
                if g.projects_data
                else {}
            )
        return g.projects_data, g.projects_dict
    return None


@cli_bp.route("/api/command/<path:command_line>")
def handle_command_api(command_line):
    """Processes a 'command' from the JS terminal via API."""
    logger.debug(f"CLI API received command: {command_line}")
    # --- Load data using the helper ---
    CV_DATA = get_cached_data("cv")
    PROJECTS_DATA, PROJECTS_DICT = get_cached_data("projects")

    parts = command_line.lower().strip().split()
    command = parts[0] if parts else ""
    args = parts[1:]

    output = []
    error = None
    terminal_width = 80  # Assume a nominal width for wrapping

    try:
        # --- Refined Command Processing Logic ---
        if command == "help":
            output.append("Available commands:")
            output.append("  whoami         - Display summary about me")
            output.append("  skills         - List my technical skills")
            output.append("  ls projects    - List available projects")
            output.append(
                "  show <project> - Show details for a project (use ID from 'ls projects')"
            )
            output.append("  links          - Show social/repository links")
            # output.append("  contact        - Display contact information") # Add contact later if needed
            output.append("  clear          - Clear the terminal screen")
            output.append("  help           - Show this help message")

        elif command == "whoami":
            if CV_DATA:
                output.append(f"Name:    {CV_DATA.get('name', 'N/A')}")
                output.append(f"Title:   {CV_DATA.get('title', 'N/A')}")
                summary = CV_DATA.get("summary", "No summary available.")
                output.append("Summary:")
                # Wrap summary text nicely
                wrapped_summary = textwrap.wrap(
                    summary, width=terminal_width - 2
                )  # Indent slightly
                output.extend([f"  {line}" for line in wrapped_summary])
            else:
                error = "Error: Could not load CV data."

        elif command == "skills":
            if CV_DATA and CV_DATA.get("skills"):
                output.append("Technical Skills:")
                # Display skills, potentially grouped or wrapped
                skills_list = CV_DATA["skills"]
                if len(skills_list) > 0:
                    # Simple comma-separated wrapping
                    skills_line = ", ".join(skills_list)
                    wrapped_skills = textwrap.wrap(
                        skills_line, width=terminal_width - 2
                    )
                    output.extend([f"  {line}" for line in wrapped_skills])
                    # Alternative: List view
                    # output.extend([f"  - {skill}" for skill in skills_list])
                else:
                    output.append("  (No skills listed in cv.yaml)")
            else:
                output.append("No skills listed or CV data unavailable.")

        elif command == "ls" and args and args[0] == "projects":
            output.append("Projects (use 'show <id>' for details):")
            if PROJECTS_DATA:
                if not PROJECTS_DATA:  # Check if list is empty
                    output.append("  (No projects found in projects.yaml)")
                else:
                    try:
                        # Calculate padding based on longest ID
                        max_id_len = max(len(p.get("id", "")) for p in PROJECTS_DATA)
                        max_id_len = max(
                            max_id_len, 4
                        )  # Ensure minimum width for 'ID' header
                        output.append(f"  {'ID':<{max_id_len}}  | Title")
                        output.append(f"  {'-' * max_id_len}  | {'-' * 20}")
                        for p in PROJECTS_DATA:
                            proj_id = p.get("id", "N/A")
                            proj_title = p.get("title", "N/A")
                            output.append(f"  {proj_id:<{max_id_len}}  | {proj_title}")
                    except Exception as e:
                        logger.error(f"Error formatting ls projects: {e}")
                        output.append("  (Error formatting project list)")
                        # Fallback basic list
                        for p in PROJECTS_DATA:
                            output.append(
                                f"  - {p.get('id', 'N/A')} : {p.get('title', 'N/A')}"
                            )
            else:
                output.append("  (Project data could not be loaded)")

        elif command == "show" and args:
            project_id = args[0]
            if not PROJECTS_DICT:
                error = "Error: Project data not loaded."
            else:
                project = PROJECTS_DICT.get(project_id)
                if project:
                    output.append(
                        f"--- Project: {project.get('title', 'N/A')} [{project.get('type', 'N/A').capitalize()}] ---"
                    )
                    desc = project.get("description", "(No description)")
                    output.append("Description:")
                    wrapped_desc = textwrap.wrap(desc, width=terminal_width - 2)
                    output.extend([f"  {line}" for line in wrapped_desc])

                    if project.get("technologies"):
                        output.append("Technologies:")
                        tech_line = ", ".join(project["technologies"])
                        wrapped_tech = textwrap.wrap(
                            tech_line, width=terminal_width - 2
                        )
                        output.extend([f"  {line}" for line in wrapped_tech])
                    else:
                        output.append("Technologies: (Not specified)")

                    output.append("Links:")
                    link_found = False
                    # Use consistent formatting for links
                    if project.get("live_url"):
                        output.append(
                            f"  - Live Demo: <link>{project['live_url']}</link>"
                        )
                        link_found = True
                    if project.get("github_url"):
                        output.append(
                            f"  - Code Repo: <link>{project['github_url']}</link>"
                        )
                        link_found = True
                    if project.get("pypi_url"):
                        output.append(
                            f"  - PyPI Page: <link>{project['pypi_url']}</link>"
                        )
                        link_found = True
                    if project.get("docs_url"):
                        output.append(
                            f"  - Docs:      <link>{project['docs_url']}</link>"
                        )
                        link_found = True

                    if not link_found:
                        output.append("  (No links available for this project)")
                else:
                    error = f"Error: Project '{project_id}' not found. Use 'ls projects' to see available IDs."

        elif command == "links":
            output.append("--- Social & Repo Links ---")
            link_found = False
            if CV_DATA and CV_DATA.get("social_links"):
                # Calculate padding for alignment
                max_key_len = (
                    max(len(key) for key in CV_DATA["social_links"].keys())
                    if CV_DATA["social_links"]
                    else 0
                )
                max_key_len = max(max_key_len, 8)  # Min width for "Platform" header?

                # output.append(f"  {'Platform':<{max_key_len}} | URL")
                # output.append(f"  {'-' * max_key_len}-+------------------") # Adjust separator length

                for key, url in CV_DATA["social_links"].items():
                    # Simple list format might be cleaner in terminal
                    output.append(f"  - {key.capitalize()}: <link>{url}</link>")
                    link_found = True
            if not link_found:
                output.append("  (No social links configured in cv.yaml)")

        elif command == "clear":
            pass  # Handled only by JS frontend
        elif command == "":
            pass  # Ignore empty command
        else:
            error = f"Error: Command not found '{command}'. Type 'help' for available commands."
        # --- End Refined Command Logic ---

    except Exception as e:
        logger.error(
            f"CLI API error processing command '{command_line}': {e}", exc_info=True
        )
        # Provide a more generic error to the user, log the details
        error = "An internal server error occurred. Please check server logs."

    # Return command for 'clear' check in JS
    return jsonify({"output": output, "error": error, "command": command})
