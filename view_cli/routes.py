import logging
import textwrap

from flask import g, jsonify

from common.utils import load_cv_data, load_projects_data

from . import cli_bp

logger = logging.getLogger(__name__)


def get_cached_data(data_type="cv"):
    """Gets cached data from Flask's 'g' context, loading if not present."""
    if data_type == "cv":
        if "cv_data" not in g:
            g.cv_data = load_cv_data()
            logger.info("CLI: CV data loaded into context g")
        return g.cv_data
    elif data_type == "projects":
        if "projects_data" not in g:
            g.projects_data, g.projects_dict = load_projects_data()
            logger.info("CLI: Projects data loaded into context g")
        elif "projects_data" in g and "projects_dict" not in g:
            g.projects_dict = (
                {p.get("id", f"proj_{i}"): p for i, p in enumerate(g.projects_data)}
                if g.projects_data
                else {}
            )
            logger.info(
                "CLI: Populated projects_dict from existing projects_data in context g"
            )
        return g.get("projects_data", []), g.get("projects_dict", {})
    return None


@cli_bp.route("/api/command/<path:command_line>")
def handle_command_api(command_line):
    """API endpoint to process a command string from the CLI view."""
    logger.debug(f"CLI API received command: {command_line}")
    CV_DATA = get_cached_data("cv")
    PROJECTS_DATA, PROJECTS_DICT = get_cached_data("projects")

    if not CV_DATA or PROJECTS_DATA is None:
        logger.error("CLI API failed: CV or Projects data not loaded into context.")
        return (
            jsonify({"output": [], "error": "[ERROR] Failed to load backend data."}),
            500,
        )

    parts = command_line.lower().strip().split()
    command = parts[0] if parts else ""
    args = parts[1:]

    output = []
    error = None
    terminal_width = 80

    try:
        if command == "help":
            output.append("[INFO] Portfolio Commands:")
            output.append("  whoami         - Display summary about me")
            output.append("  skills         - List my technical skills")
            output.append("  contact        - Show contact information")
            output.append("  links          - Show social and repository links")
            output.append("  ls projects    - List available projects")
            output.append("  show <project> - Show details for a specific project")
            output.append("")
            output.append("[INFO] Window Management Commands:")
            output.append("  maximize       - Maximize the terminal window")
            output.append("  minimize       - Minimize the terminal window")
            output.append("  restore        - Restore window from min/max state")
            output.append(
                "  win-reset      - Reset window to default size and position"
            )
            output.append("  clear          - Clear the terminal screen")
            output.append("  exit / close   - Close the terminal window")

        elif command == "whoami":
            output.append(f"Name:    {CV_DATA.get('name', 'N/A')}")
            output.append(f"Title:   {CV_DATA.get('title', 'N/A')}")
            summary = CV_DATA.get("summary", "No summary available.")
            output.append("Summary:")
            wrapped_summary = textwrap.wrap(
                summary, width=terminal_width - 2, subsequent_indent="  "
            )
            output.extend(wrapped_summary)

        elif command == "skills":
            output.append("[INFO] Technical Skills:")
            if CV_DATA.get("skills"):
                skills_list = CV_DATA["skills"]
                if len(skills_list) > 0:
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

        elif command == "contact":
            output.append("[INFO] Contact Information:")
            contact_found = False
            if CV_DATA.get("email"):
                output.append(f"  - Email:    <link>mailto:{CV_DATA['email']}</link>")
                contact_found = True
            social_links = CV_DATA.get("social_links", {})
            if social_links.get("linkedin"):
                output.append(f"  - LinkedIn: <link>{social_links['linkedin']}</link>")
                contact_found = True
            if social_links.get("github"):
                output.append(f"  - GitHub:   <link>{social_links['github']}</link>")
                contact_found = True
            if CV_DATA.get("website"):
                output.append(f"  - Website:  <link>{CV_DATA['website']}</link>")
                contact_found = True
            if not contact_found:
                output.append("  (No contact details available in cv.yaml)")

        elif command == "ls" and args and args[0] == "projects":
            output.append("[INFO] Projects (use 'show <id>' for details):")
            if PROJECTS_DATA:
                if not PROJECTS_DATA:
                    output.append("  (No projects found in projects.yaml)")
                else:
                    try:
                        max_id_len = max(len(p.get("id", "")) for p in PROJECTS_DATA)
                        max_id_len = max(max_id_len, 4)
                        output.append(f"  {'ID'.ljust(max_id_len)}  | Title")
                        output.append(f"  {'-' * max_id_len}  + {'-' * 40}")
                        for p in PROJECTS_DATA:
                            proj_id = p.get("id", "N/A")
                            proj_title = p.get("title", "N/A")
                            output.append(
                                f"  {proj_id.ljust(max_id_len)}  | {proj_title}"
                            )
                    except Exception as e:
                        logger.error(f"Error formatting ls projects: {e}")
                        output.append("  (Error formatting project list)")
                        for p in PROJECTS_DATA:
                            output.append(
                                f"  - {p.get('id', 'N/A')} : {p.get('title', 'N/A')}"
                            )
            else:
                output.append("  (Project data could not be loaded)")

        elif command == "show" and args:
            project_id = args[0]
            if PROJECTS_DICT is None:
                error = "[ERROR] Project data dictionary not loaded."
            else:
                project = PROJECTS_DICT.get(project_id)
                if project:
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

                    output.append("[LINK] Links:")
                    link_found = False
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
                    error = (
                        f"[ERROR] Project '{project_id}' not found. Use 'ls projects'."
                    )

        elif command == "links":
            output.append("[INFO] Social & Repo Links:")
            link_found = False
            social_links = CV_DATA.get("social_links", {})
            if social_links:
                for key, url in social_links.items():
                    platform_name = key.replace("_", " ").capitalize()
                    output.append(f"  - {platform_name}: <link>{url}</link>")
                    link_found = True
            if not link_found:
                output.append("  (No social links configured)")

        elif command == "":
            pass
        else:
            error = f"[ERROR] Command not found: '{command}'. Type 'help'."

    except Exception as e:
        logger.error(
            f"CLI API exception processing command '{command_line}': {e}",
            exc_info=True,
        )
        error = "[ERROR] Internal server error occurred. Please check server logs."

    return jsonify({"output": output, "error": error, "command": command})
