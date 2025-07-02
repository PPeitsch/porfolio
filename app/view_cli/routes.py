import logging
import textwrap
from typing import Any, Dict, List, Tuple

from flask import g, jsonify

from app.common.decorators import token_required
from app.common.utils import (
    _get_data_filepath,
    load_cv_data,
    load_projects_data,
    load_text_config,
)

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


# --- Command Handler Functions ---


def _handle_help(text_config: Dict[str, Any], **kwargs: Any) -> Tuple[List[str], None]:
    output = []
    help_config = text_config.get("cli", {}).get("commands", {})
    output.append(help_config.get("portfolio_header", "Portfolio Commands:"))

    portfolio_commands = [
        item
        for item in help_config.get("items", [])
        if item.get("group") == "portfolio"
    ]
    max_cmd_len = (
        max(len(c["command"]) for c in portfolio_commands) if portfolio_commands else 0
    )
    for cmd in portfolio_commands:
        output.append(f"  {cmd['command'].ljust(max_cmd_len)} - {cmd['description']}")

    output.append("")
    output.append(help_config.get("system_header", "System Commands:"))

    system_commands = [
        item for item in help_config.get("items", []) if item.get("group") == "system"
    ]
    max_cmd_len = (
        max(len(c["command"]) for c in system_commands) if system_commands else 0
    )
    for cmd in system_commands:
        output.append(f"  {cmd['command'].ljust(max_cmd_len)} - {cmd['description']}")
    return output, None


def _handle_whoami(
    cv_data: Dict[str, Any], terminal_width: int, **kwargs: Any
) -> Tuple[List[str], None]:
    output = [
        f"Name:    {cv_data.get('name', 'N/A')}",
        f"Title:   {cv_data.get('title', 'N/A')}",
        "Summary:",
    ]
    summary = cv_data.get("summary", "No summary available.")
    wrapped_summary = textwrap.wrap(
        summary, width=terminal_width - 2, subsequent_indent="  "
    )
    output.extend(wrapped_summary)
    return output, None


def _handle_skills(
    cv_data: Dict[str, Any], terminal_width: int, **kwargs: Any
) -> Tuple[List[str], None]:
    output = ["[INFO] Technical Skills:"]
    skills_list = cv_data.get("skills", [])
    if skills_list:
        skills_line = ", ".join(skills_list)
        wrapped_skills = textwrap.wrap(
            skills_line,
            width=terminal_width - 2,
            initial_indent="  ",
            subsequent_indent="  ",
        )
        output.extend(wrapped_skills)
    else:
        output.append("  (Skills data unavailable)")
    return output, None


def _handle_contact(cv_data: Dict[str, Any], **kwargs: Any) -> Tuple[List[str], None]:
    output = ["[INFO] Contact Information:"]
    contact_found = False
    if cv_data.get("email"):
        output.append(f"  - Email:    <link>mailto:{cv_data['email']}</link>")
        contact_found = True
    social_links = cv_data.get("social_links", {})
    if social_links.get("linkedin"):
        output.append(f"  - LinkedIn: <link>{social_links['linkedin']}</link>")
        contact_found = True
    if social_links.get("github"):
        output.append(f"  - GitHub:   <link>{social_links['github']}</link>")
        contact_found = True
    if cv_data.get("website"):
        output.append(f"  - Website:  <link>{cv_data['website']}</link>")
        contact_found = True
    if not contact_found:
        output.append("  (No contact details available)")
    return output, None


def _handle_ls(
    args: List[str], projects_data: List[Dict[str, Any]], **kwargs: Any
) -> Tuple[List[str] | None, str | None]:
    if not args or args[0] != "projects":
        return None, "[ERROR] Unknown argument for 'ls'. Did you mean 'ls projects'?"

    output = ["[INFO] Projects (use 'show <id>' for details):"]
    if projects_data:
        try:
            max_id_len = max(len(p.get("id", "")) for p in projects_data)
            max_id_len = max(max_id_len, 4)
            output.append(f"  {'ID'.ljust(max_id_len)}  | Title")
            output.append(f"  {'-' * max_id_len}  + {'-' * 40}")
            for p in projects_data:
                proj_id = p.get("id", "N/A")
                proj_title = p.get("title", "N/A")
                output.append(f"  {proj_id.ljust(max_id_len)}  | {proj_title}")
        except Exception as e:
            logger.error(f"Error formatting ls projects: {e}")
            output.append("  (Error formatting project list)")
    else:
        output.append("  (Project data could not be loaded)")
    return output, None


def _handle_filter(
    args: List[str], projects_data: List[Dict[str, Any]], **kwargs: Any
) -> Tuple[List[str] | None, str | None]:
    if len(args) < 2 or args[0] != "--tech":
        return (
            None,
            "[ERROR] Usage: filter --tech <technology>. Example: filter --tech python",
        )

    tech_to_filter = args[1].lower()
    filtered_projects = [
        p
        for p in projects_data
        if tech_to_filter in [tech.lower() for tech in p.get("technologies", [])]
    ]

    if not filtered_projects:
        output = [f"[INFO] No projects found with technology: '{tech_to_filter}'"]
        return output, None

    output = [f"[INFO] Projects using '{tech_to_filter.capitalize()}':"]
    try:
        max_id_len = max(len(p.get("id", "")) for p in filtered_projects)
        max_id_len = max(max_id_len, 4)
        output.append(f"  {'ID'.ljust(max_id_len)}  | Title")
        output.append(f"  {'-' * max_id_len}  + {'-' * 40}")
        for p in filtered_projects:
            proj_id = p.get("id", "N/A")
            proj_title = p.get("title", "N/A")
            output.append(f"  {proj_id.ljust(max_id_len)}  | {proj_title}")
    except Exception as e:
        logger.error(f"Error formatting filtered projects: {e}")
        output.append("  (Error formatting project list)")

    return output, None


def _handle_show(
    args: List[str],
    projects_dict: Dict[str, Any],
    terminal_width: int,
    **kwargs: Any,
) -> Tuple[List[str] | None, str | None]:
    if not args:
        return None, "[ERROR] Usage: show <project_id>"
    project_id = args[0]
    project = projects_dict.get(project_id)

    if not project:
        return None, f"[ERROR] Project '{project_id}' not found. Use 'ls projects'."

    output = [
        f"--- Project: {project.get('title', 'N/A')} ---",
        f"[INFO] Type: {project.get('type', 'N/A').capitalize()}",
        "[INFO] Description:",
    ]
    desc = project.get("description", "(No description)")
    output.extend(
        textwrap.wrap(
            desc,
            width=terminal_width - 2,
            initial_indent="  ",
            subsequent_indent="  ",
        )
    )

    technologies = project.get("technologies")
    output.append("[INFO] Technologies:")
    if technologies:
        tech_line = ", ".join(technologies)
        output.extend(
            textwrap.wrap(
                tech_line,
                width=terminal_width - 2,
                initial_indent="  ",
                subsequent_indent="  ",
            )
        )
    else:
        output.append("  (Not specified)")

    output.append("[LINK] Links:")
    link_found = False
    for key, name in [
        ("live_url", "Live Demo"),
        ("github_url", "Code Repo"),
        ("pypi_url", "PyPI Page"),
        ("docs_url", "Docs"),
    ]:
        if url := project.get(key):
            output.append(f"  - {name:<11}: <link>{url}</link>")
            link_found = True
    if not link_found:
        output.append("  (No external links available)")

    return output, None


def _handle_open(
    args: List[str], projects_dict: Dict[str, Any], **kwargs: Any
) -> Tuple[List[str] | None, str | None, Dict[str, Any] | None]:
    if not args:
        return None, "[ERROR] Usage: open <project_id>", None
    project_id = args[0]
    project = projects_dict.get(project_id)

    if not project:
        return None, f"[ERROR] Project '{project_id}' not found.", None

    url = project.get("live_url")
    if not url:
        return (
            None,
            f"[INFO] Project '{project_id}' does not have a live URL to open.",
            None,
        )

    action_payload = {"action": "open_url", "url": url}
    output = [f"Attempting to open {url} in a new tab..."]
    return output, None, action_payload


def _handle_links(cv_data: Dict[str, Any], **kwargs: Any) -> Tuple[List[str], None]:
    output = ["[INFO] Social & Repo Links:"]
    social_links = cv_data.get("social_links", {})
    if social_links:
        for key, url in social_links.items():
            platform_name = key.replace("_", " ").capitalize()
            output.append(f"  - {platform_name}: <link>{url}</link>")
    else:
        output.append("  (No social links configured)")
    return output, None


def _handle_uname(text_config: Dict[str, Any], **kwargs: Any) -> Tuple[List[str], None]:
    uname_text = text_config.get("cli", {}).get(
        "uname", "FlaskOS 1.0 Portfolio x86_64 GNU/Linux-like"
    )
    return [uname_text], None


def _handle_neofetch(
    cv_data: Dict[str, Any],
    projects_data: List[Dict[str, Any]],
    text_config: Dict[str, Any],
    **kwargs: Any,
) -> Tuple[List[str], None]:
    name = cv_data.get("name", "N/A")
    title = cv_data.get("title", "N/A")
    project_count = len(projects_data)
    skill_count = len(cv_data.get("skills", []))

    neofetch_config = text_config.get("cli", {}).get("neofetch", {})
    host_template = neofetch_config.get("host_template", "{name}'s Portfolio")

    logo = []
    try:
        logo_path = _get_data_filepath("logo/neofetch_logo_bear.txt")
        with open(logo_path, "r", encoding="utf-8") as f:
            logo = [line.rstrip() for line in f.readlines()]
    except FileNotFoundError:
        logo = ["(Logo not found)"]

    info = [
        f"{name}@{cv_data.get('website', 'localhost')}",
        "-----------------------",
        f"OS: {neofetch_config.get('os_name', 'FlaskOS Portfolio')}",
        f"Host: {host_template.format(name=name)}",
        f"Title: {title}",
        f"Projects: {project_count}",
        f"Skills: {skill_count}",
        f"Shell: {neofetch_config.get('shell_name', 'Web-CLI')}",
    ]
    max_logo_width = max(len(line) for line in logo) if logo else 0
    logo_vertical_offset = 1
    num_lines = max(len(logo) + logo_vertical_offset, len(info))
    output = []
    for i in range(num_lines):
        info_line = info[i] if i < len(info) else ""
        logo_index = i - logo_vertical_offset
        logo_line = logo[logo_index] if 0 <= logo_index < len(logo) else ""
        padded_logo_line = logo_line.ljust(max_logo_width)
        output.append(f"{padded_logo_line}  {info_line}")
    return output, None


def _handle_man(
    args: List[str], text_config: Dict[str, Any], **kwargs: Any
) -> Tuple[List[str] | None, str | None]:
    if not args:
        return None, "[ERROR] Usage: man <command>. Please specify a command."
    command_name = args[0].lower()
    manuals = text_config.get("cli", {}).get("manuals", {})
    manual_text = manuals.get(command_name)
    if not manual_text:
        return None, f"[ERROR] No manual entry for '{command_name}'."
    return manual_text, None


# --- Main Command Dispatcher ---

COMMAND_HANDLERS = {
    "help": _handle_help,
    "whoami": _handle_whoami,
    "skills": _handle_skills,
    "contact": _handle_contact,
    "ls": _handle_ls,
    "filter": _handle_filter,
    "show": _handle_show,
    "open": _handle_open,
    "links": _handle_links,
    "uname": _handle_uname,
    "neofetch": _handle_neofetch,
    "man": _handle_man,
}


@cli_bp.route("/api/command/<path:command_line>")
@token_required
def handle_command_api(command_line):
    """API endpoint to process a command string from the CLI view."""
    logger.debug(f"CLI API received command: {command_line}")
    CV_DATA = get_cached_data("cv")
    PROJECTS_DATA, PROJECTS_DICT = get_cached_data("projects")
    TEXT_CONFIG = load_text_config()

    if not CV_DATA or PROJECTS_DATA is None:
        logger.error("CLI API failed: CV or Projects data not loaded into context.")
        return (
            jsonify({"output": [], "error": "[ERROR] Failed to load backend data."}),
            500,
        )

    parts = command_line.lower().strip().split()
    command = parts[0] if parts else ""
    args = parts[1:]

    output, error, action = [], None, None
    terminal_width = 80

    try:
        if command == "uname" and args == ["-a"]:
            handler = COMMAND_HANDLERS.get("uname")
        else:
            handler = COMMAND_HANDLERS.get(command)

        if handler:
            context = {
                "cv_data": CV_DATA,
                "projects_data": PROJECTS_DATA,
                "projects_dict": PROJECTS_DICT,
                "text_config": TEXT_CONFIG,
                "args": args,
                "terminal_width": terminal_width,
            }
            handler_result = handler(**context)

            # Unpack result based on its length for backward compatibility
            if len(handler_result) == 3:
                output, error, action = handler_result
            else:
                output, error = handler_result

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

    response_data = {"output": output or [], "error": error, "command": command}
    if action:
        response_data.update(action)

    prompt_config = TEXT_CONFIG.get("cli", {}).get("prompt", {})
    response_data["prompt"] = prompt_config

    return jsonify(response_data)
