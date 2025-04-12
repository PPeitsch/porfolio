import logging
import os
import textwrap  # For wrapping long descriptions

from flask import abort, g, jsonify, send_from_directory

from common.utils import load_cv_data, load_projects_data

from . import cli_bp  # Import the blueprint defined in __init__.py

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
    static_dir = os.path.join(
        os.path.dirname(__file__), "static"
    )  # Relative to this routes.py file
    logger.debug(f"Serving CLI static file: {filename} from {static_dir}")
    try:
        return send_from_directory(static_dir, filename)
    except FileNotFoundError:
        logger.error(f"CLI Static file not found: {os.path.join(static_dir, filename)}")
        abort(404)


# --- API Endpoint for CLI Commands (Enhanced) ---
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
        # Return error in JSON format for JS
        return (
            jsonify({"output": [], "error": "[ERROR] Failed to load backend data."}),
            500,
        )

    parts = command_line.lower().strip().split()
    command = parts[0] if parts else ""
    args = parts[1:]

    output = []
    error = None
    terminal_width = 80  # Approximate width for formatting

    try:
        # --- Refined Command Processing Logic ---
        if command == "help":
            output.append("[INFO] Available commands:")  # Use markers
            output.append("  whoami         - Display summary about me")
            output.append("  skills         - List my technical skills")
            output.append(
                "  contact        - Show contact information"
            )  # Added command
            output.append("  ls projects    - List available projects")
            output.append("  show <project> - Show details for a project (use ID)")
            output.append("  links          - Show social/repository links")
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
            output.append("[INFO] Technical Skills:")
            if CV_DATA.get("skills"):
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
                output.append("  (Skills data unavailable)")

        # --- NEW: Contact Command ---
        elif command == "contact":
            output.append("[INFO] Contact Information:")
            contact_found = False
            # Check for email in main CV data first
            if CV_DATA.get("email"):
                # Use mailto: for clickable email links
                output.append(f"  - Email:    <link>mailto:{CV_DATA['email']}</link>")
                contact_found = True
            # Check social links section for others
            social_links = CV_DATA.get("social_links", {})
            if social_links.get("linkedin"):
                output.append(f"  - LinkedIn: <link>{social_links['linkedin']}</link>")
                contact_found = True
            if social_links.get("github"):  # GitHub often in social links
                output.append(f"  - GitHub:   <link>{social_links['github']}</link>")
                contact_found = True
            # Add website if present in main CV data
            if CV_DATA.get("website"):
                output.append(f"  - Website:  <link>{CV_DATA['website']}</link>")
                contact_found = True

            if not contact_found:
                output.append("  (No contact details available in cv.yaml)")

        elif command == "ls" and args and args[0] == "projects":
            output.append("[INFO] Projects (use 'show <id>' for details):")
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

        # --- ENHANCED: Show Command ---
        elif command == "show" and args:
            project_id = args[0]
            if PROJECTS_DICT is None:  # Check if dict loading failed
                error = "[ERROR] Project data dictionary not loaded."
            else:
                project = PROJECTS_DICT.get(project_id)
                if project:
                    # Use markers for sections
                    output.append(f"--- Project: {project.get('title', 'N/A')} ---")
                    output.append(
                        f"[INFO] Type: {project.get('type', 'N/A').capitalize()}"
                    )
                    desc = project.get("description", "(No description)")
                    output.append("[INFO] Description:")
                    wrapped_desc = textwrap.wrap(
                        desc,
                        width=terminal_width - 2,
                        initial_indent="  ",
                        subsequent_indent="  ",
                    )
                    output.extend(wrapped_desc)

                    technologies = project.get("technologies")
                    if technologies:
                        output.append("[INFO] Technologies:")
                        # Use simple comma join for CLI, maybe wrap
                        tech_line = ", ".join(technologies)
                        wrapped_tech = textwrap.wrap(
                            tech_line,
                            width=terminal_width - 2,
                            initial_indent="  ",
                            subsequent_indent="  ",
                        )
                        output.extend(wrapped_tech)
                    else:
                        output.append("[INFO] Technologies: (Not specified)")

                    output.append("[LINK] Links:")  # Use marker
                    link_found = False
                    # Use descriptive labels
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
                        output.append("  (No external links available)")
                else:
                    # Use marker for error
                    error = f"[ERROR] Project '{project_id}' not found. Use 'ls projects' for IDs."

        elif command == "links":
            output.append("[INFO] Social & Repo Links:")
            link_found = False
            # Prefer social_links structure if present
            if CV_DATA.get("social_links"):
                for key, url in CV_DATA["social_links"].items():
                    platform_name = key.replace("_", " ").capitalize()
                    output.append(f"  - {platform_name}: <link>{url}</link>")
                    link_found = True
            # Fallback to top-level keys if social_links missing but others exist
            elif CV_DATA.get("github") or CV_DATA.get("linkedin"):
                if CV_DATA.get("linkedin"):
                    output.append(f"  - LinkedIn: <link>{CV_DATA['linkedin']}</link>")
                    link_found = True
                if CV_DATA.get("github"):
                    output.append(f"  - GitHub:   <link>{CV_DATA['github']}</link>")
                    link_found = True
            # Add website if present
            if CV_DATA.get("website"):
                output.append(f"  - Website:  <link>{CV_DATA['website']}</link>")
                link_found = True

            if not link_found:
                output.append("  (No social links configured in cv.yaml)")

        elif command == "clear":
            # Command acknowledged by API, but action is frontend only
            pass
        elif command == "":
            # No output for empty command
            pass
        else:
            # Command not recognized
            error = (
                f"[ERROR] Command not found: '{command}'. Type 'help'."  # Use marker
            )
        # --- End Refined Command Logic ---

    except Exception as e:
        # Log the full error traceback for server-side debugging
        logger.error(
            f"CLI API exception processing command '{command_line}': {e}", exc_info=True
        )
        # Provide a more generic error message to the user
        error = "[ERROR] Internal server error occurred. Please check server logs."  # Use marker

    # Return JSON response including the original command (useful for 'clear')
    return jsonify({"output": output, "error": error, "command": command})
