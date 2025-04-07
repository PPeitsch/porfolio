from flask import jsonify, current_app, g, send_from_directory, abort
from . import cli_bp  # Import the blueprint defined in __init__.py
from common.utils import load_cv_data, load_projects_data  # Import shared utils
import logging
import textwrap  # For wrapping long descriptions
import os  # For constructing static path

logger = logging.getLogger(__name__)


# --- Helper to get cached data within the context of this blueprint ---
def get_cached_data(data_type="cv"):
    """Helper to load data once per app context for CLI."""
    # Use Flask's application context global 'g'
    if data_type == "cv":
        if "cv_data" not in g:
            g.cv_data = load_cv_data()  # Assumes load_cv_data is robust
            logger.info("CLI: CV data loaded into context g")
        return g.cv_data
    elif data_type == "projects":
        if "projects_data" not in g:
            g.projects_data, g.projects_dict = (
                load_projects_data()
            )  # Assumes this returns tuple
            logger.info("CLI: Projects data loaded into context g")
        # Ensure projects_dict is populated if projects_data exists from previous g context
        elif "projects_data" in g and "projects_dict" not in g:
            g.projects_dict = (
                {p.get("id", f"proj_{i}"): p for i, p in enumerate(g.projects_data)}
                if g.projects_data
                else {}
            )
            logger.info(
                "CLI: Populated projects_dict from existing projects_data in context g"
            )
        # Return potentially empty list/dict if loading failed or no data
        return g.get("projects_data", []), g.get("projects_dict", {})
    return None


# --- Route to serve static files for this blueprint ---
@cli_bp.route("/static/<path:filename>")
def static_files(filename):
    """Serves static files specific to the CLI blueprint."""
    # Construct path relative to the blueprint's root path (directory of __init__.py)
    # static_dir = os.path.join(cli_bp.root_path, 'static') # Alternative way
    static_dir = os.path.join(
        os.path.dirname(__file__), "static"
    )  # Relative to this routes.py file
    logger.debug(f"Serving CLI static file: {filename} from {static_dir}")
    try:
        return send_from_directory(static_dir, filename)
    except FileNotFoundError:
        logger.error(f"CLI Static file not found: {os.path.join(static_dir, filename)}")
        abort(404)


# --- API Endpoint for CLI Commands ---
@cli_bp.route("/api/command/<path:command_line>")
def handle_command_api(command_line):
    """Processes a 'command' from the JS terminal via API."""
    logger.debug(f"CLI API received command: {command_line}")
    # --- Load data using the helper ---
    CV_DATA = get_cached_data("cv")
    PROJECTS_DATA, PROJECTS_DICT = get_cached_data("projects")

    # Basic check if data loading failed severely upstream
    if not CV_DATA or PROJECTS_DATA is None:  # PROJECTS_DATA can be empty list
        logger.error("CLI API failed: CV or Projects data not loaded into context.")
        return (
            jsonify(
                {
                    "output": [],
                    "error": "Error: Failed to load backend data. Check server logs.",
                }
            ),
            500,
        )

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
            output.append(f"Name:    {CV_DATA.get('name', 'N/A')}")
            output.append(f"Title:   {CV_DATA.get('title', 'N/A')}")
            summary = CV_DATA.get("summary", "No summary available.")
            output.append("Summary:")
            # Wrap summary text nicely
            wrapped_summary = textwrap.wrap(
                summary, width=terminal_width - 2, subsequent_indent="  "
            )  # Indent subsequent lines
            output.extend(wrapped_summary)  # Add wrapped lines directly

        elif command == "skills":
            if CV_DATA.get("skills"):
                output.append("Technical Skills:")
                skills_list = CV_DATA["skills"]
                if len(skills_list) > 0:
                    # Simple comma-separated wrapping
                    skills_line = ", ".join(skills_list)
                    wrapped_skills = textwrap.wrap(
                        skills_line,
                        width=terminal_width - 2,
                        initial_indent="  ",
                        subsequent_indent="  ",
                    )
                    output.extend(wrapped_skills)
                else:
                    output.append("  (No skills listed in cv.yaml)")
            else:
                output.append("No skills listed or CV data unavailable.")

        elif command == "ls" and args and args[0] == "projects":
            output.append("Projects (use 'show <id>' for details):")
            if PROJECTS_DATA:  # Checks if list is not None
                if not PROJECTS_DATA:  # Check if list is empty
                    output.append("  (No projects found in projects.yaml)")
                else:
                    try:
                        # Calculate padding based on longest ID
                        max_id_len = max(len(p.get("id", "")) for p in PROJECTS_DATA)
                        max_id_len = max(
                            max_id_len, 4
                        )  # Ensure minimum width for 'ID' header
                        # Header
                        output.append(f"  {'ID'.ljust(max_id_len)}  | Title")
                        output.append(
                            f"  {'-' * max_id_len}  + {'-' * 40}"
                        )  # Separator line
                        # Project rows
                        for p in PROJECTS_DATA:
                            proj_id = p.get("id", "N/A")
                            proj_title = p.get("title", "N/A")
                            output.append(
                                f"  {proj_id.ljust(max_id_len)}  | {proj_title}"
                            )
                    except Exception as e:
                        logger.error(f"Error formatting ls projects: {e}")
                        output.append("  (Error formatting project list)")
                        # Fallback basic list if formatting fails
                        for p in PROJECTS_DATA:
                            output.append(
                                f"  - {p.get('id', 'N/A')} : {p.get('title', 'N/A')}"
                            )
            else:
                # This case should ideally not be reached if get_cached_data ensures list return
                output.append("  (Project data could not be loaded or is unavailable)")

        elif command == "show" and args:
            project_id = args[0]
            if PROJECTS_DICT is None:  # Check if dict loading failed
                error = "Error: Project data dictionary not loaded."
            else:
                project = PROJECTS_DICT.get(project_id)
                if project:
                    output.append(
                        f"--- Project: {project.get('title', 'N/A')} [{project.get('type', 'N/A').capitalize()}] ---"
                    )
                    desc = project.get("description", "(No description)")
                    output.append("Description:")
                    wrapped_desc = textwrap.wrap(
                        desc,
                        width=terminal_width - 2,
                        initial_indent="  ",
                        subsequent_indent="  ",
                    )
                    output.extend(wrapped_desc)

                    technologies = project.get("technologies")
                    if technologies:
                        output.append("Technologies:")
                        # Format with brackets like [Tech1], [Tech2]
                        tech_tags = " ".join([f"[{t}]" for t in technologies])
                        wrapped_tech = textwrap.wrap(
                            tech_tags,
                            width=terminal_width - 2,
                            initial_indent="  ",
                            subsequent_indent="  ",
                        )
                        output.extend(wrapped_tech)
                    else:
                        output.append("Technologies: (Not specified)")

                    output.append("Links:")
                    link_found = False
                    # Use consistent formatting and labels for links
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
                        output.append(
                            "  (No external links available for this project)"
                        )
                else:
                    error = f"Error: Project '{project_id}' not found. Use 'ls projects' to see available IDs."

        elif command == "links":
            output.append("--- Social & Repo Links ---")
            link_found = False
            if CV_DATA.get("social_links"):
                # Simple list format for clarity
                for key, url in CV_DATA["social_links"].items():
                    # Format key nicely (e.g., 'github' -> 'GitHub')
                    platform_name = key.replace("_", " ").capitalize()
                    output.append(f"  - {platform_name}: <link>{url}</link>")
                    link_found = True
            else:  # CV_DATA loaded but no social_links key
                output.append("  (No social links configured in cv.yaml)")

            if not link_found and not CV_DATA.get(
                "social_links"
            ):  # Handles case where CV_DATA itself failed
                output.append("  (Could not load social link data)")

        elif command == "clear":
            # Command acknowledged by API, but action is frontend only
            pass
        elif command == "":
            # No output for empty command
            pass
        else:
            # Command not recognized
            error = f"Error: Command not found '{command}'. Type 'help' for available commands."
        # --- End Refined Command Logic ---

    except Exception as e:
        # Log the full error traceback for server-side debugging
        logger.error(
            f"CLI API exception processing command '{command_line}': {e}", exc_info=True
        )
        # Provide a more generic error message to the user
        error = (
            "An internal server error occurred. Please check server logs for details."
        )

    # Return JSON response including the original command (useful for 'clear')
    return jsonify({"output": output, "error": error, "command": command})
