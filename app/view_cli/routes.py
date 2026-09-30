import logging
import re
import textwrap
from typing import Any, Dict, List, Tuple

from flask import g, jsonify

from app.common.decorators import token_required
from app.common.i18n import t
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

    def get_cmd_base(c):
        # Helper to get command name without arguments for alignment calculation
        return re.sub(r"\s<.*>", "", c["command"])

    # --- Portfolio Commands ---
    output.append(help_config.get("portfolio_header", "Portfolio Commands:"))
    portfolio_commands = [
        item
        for item in help_config.get("items", [])
        if item.get("group") == "portfolio"
    ]
    max_cmd_len = (
        max(len(get_cmd_base(c)) for c in portfolio_commands)
        if portfolio_commands
        else 0
    )
    for cmd in portfolio_commands:
        command_str = cmd["command"]
        # Calculate padding needed to align descriptions
        padding = max_cmd_len + (len(command_str) - len(get_cmd_base(cmd)))
        line = f"  {command_str.ljust(padding)} - {cmd['description']}"
        output.append(line)

    output.append("")

    # --- System Commands ---
    output.append(help_config.get("system_header", "System Commands:"))

    system_commands = [
        item for item in help_config.get("items", []) if item.get("group") == "system"
    ]
    max_cmd_len = (
        max(len(get_cmd_base(c)) for c in system_commands) if system_commands else 0
    )
    for cmd in system_commands:
        command_str = cmd["command"]
        padding = max_cmd_len + (len(command_str) - len(get_cmd_base(cmd)))
        line = f"  {command_str.ljust(padding)} - {cmd['description']}"
        output.append(line)

    return output, None


def _handle_whoami(
    cv_data: Dict[str, Any], terminal_width: int, **kwargs: Any
) -> Tuple[List[str], None]:
    labels = [t("cli_out.name"), t("cli_out.title")]
    width = max(len(label) for label in labels) + 4
    output = [
        f"{(labels[0] + ':').ljust(width)}{cv_data.get('name', 'N/A')}",
        f"{(labels[1] + ':').ljust(width)}{cv_data.get('title', 'N/A')}",
        f"{t('cli_out.summary')}:",
    ]
    summary = cv_data.get("summary") or t("cli_out.no_summary")
    wrapped_summary = textwrap.wrap(
        summary, width=terminal_width - 2, subsequent_indent="  "
    )
    output.extend(wrapped_summary)
    return output, None


def _handle_skills(
    cv_data: Dict[str, Any], terminal_width: int, **kwargs: Any
) -> Tuple[List[str], None]:
    output = [t("cli_out.skills_header")]
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
        output.append(t("cli_out.skills_unavailable"))
    return output, None


def _handle_contact(cv_data: Dict[str, Any], **kwargs: Any) -> Tuple[List[str], None]:
    output = [t("cli_out.contact_header")]
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
        output.append(t("cli_out.contact_none"))
    return output, None


def _format_project_table(projects: List[Dict[str, Any]]) -> List[str]:
    """Formats projects as an 'ID | Title' table.

    IDs and titles are turned into strings, since YAML may load an ID like
    2024 as a number.
    """
    rows = [
        (str(p.get("id", "N/A")), str(p.get("title", "N/A")))
        for p in projects
        if isinstance(p, dict)
    ]
    id_width = max([4] + [len(proj_id) for proj_id, _ in rows])
    table = [
        f"  {'ID'.ljust(id_width)}  | {t('cli_out.table_title')}",
        f"  {'-' * id_width}  + {'-' * 40}",
    ]
    table.extend(f"  {proj_id.ljust(id_width)}  | {title}" for proj_id, title in rows)
    return table


def _handle_ls(
    args: List[str], projects_data: List[Dict[str, Any]], **kwargs: Any
) -> Tuple[List[str] | None, str | None]:
    if not args or args[0] != "projects":
        return None, t("cli_out.ls_usage")

    output = [t("cli_out.ls_header")]
    if projects_data:
        output.extend(_format_project_table(projects_data))
    else:
        output.append(t("cli_out.projects_unavailable"))
    return output, None


def _handle_filter(
    args: List[str], projects_data: List[Dict[str, Any]], **kwargs: Any
) -> Tuple[List[str] | None, str | None]:
    if len(args) < 2 or args[0] != "--tech":
        return None, t("cli_out.filter_usage")

    tech_to_filter = args[1].lower()
    filtered_projects = [
        p
        for p in projects_data
        if tech_to_filter in [str(tech).lower() for tech in p.get("technologies", [])]
    ]

    if not filtered_projects:
        output = [t("cli_out.filter_none", tech=tech_to_filter)]
        return output, None

    output = [t("cli_out.filter_header", tech=tech_to_filter.capitalize())]
    output.extend(_format_project_table(filtered_projects))

    return output, None


def _handle_show(
    args: List[str],
    projects_dict: Dict[str, Any],
    terminal_width: int,
    **kwargs: Any,
) -> Tuple[List[str] | None, str | None]:
    if not args:
        return None, t("cli_out.show_usage")
    project_id = args[0]
    project = projects_dict.get(project_id)

    if not project:
        return None, t("cli_out.show_not_found", id=project_id)

    output = [
        t("cli_out.show_header", title=project.get("title", "N/A")),
        t("cli_out.type", type=str(project.get("type", "N/A")).capitalize()),
        t("cli_out.description"),
    ]
    desc = project.get("description") or t("cli_out.no_description")
    output.extend(
        textwrap.wrap(
            desc,
            width=terminal_width - 2,
            initial_indent="  ",
            subsequent_indent="  ",
        )
    )

    technologies = project.get("technologies")
    output.append(t("cli_out.technologies"))
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
        output.append(t("cli_out.not_specified"))

    output.append(t("cli_out.links"))
    link_found = False
    link_names = [
        ("live_url", t("cli_out.link_live")),
        ("github_url", t("cli_out.link_code")),
        ("pypi_url", t("cli_out.link_pypi")),
        ("docs_url", t("cli_out.link_docs")),
    ]
    name_width = max(len(name) for _, name in link_names)
    for key, name in link_names:
        if url := project.get(key):
            output.append(f"  - {name.ljust(name_width)}: <link>{url}</link>")
            link_found = True
    if not link_found:
        output.append(t("cli_out.no_links"))

    return output, None


def _handle_open(
    args: List[str], projects_dict: Dict[str, Any], **kwargs: Any
) -> Tuple[List[str] | None, str | None, Dict[str, Any] | None]:
    if not args:
        return None, t("cli_out.open_usage"), None
    project_id = args[0]
    project = projects_dict.get(project_id)

    if not project:
        return None, t("cli_out.open_not_found", id=project_id), None

    url = project.get("live_url")
    if not url:
        return (
            None,
            t("cli_out.open_no_url", id=project_id),
            None,
        )

    action_payload = {"action": "open_url", "url": url}
    output = [t("cli_out.opening", url=url)]
    return output, None, action_payload


def _handle_links(cv_data: Dict[str, Any], **kwargs: Any) -> Tuple[List[str], None]:
    output = [t("cli_out.links_header")]
    social_links = cv_data.get("social_links", {})
    if social_links:
        for key, url in social_links.items():
            platform_name = key.replace("_", " ").capitalize()
            output.append(f"  - {platform_name}: <link>{url}</link>")
    else:
        output.append(t("cli_out.links_none"))
    return output, None


def _handle_uname(text_config: Dict[str, Any], **kwargs: Any) -> Tuple[List[str], None]:
    uname_text = text_config.get("cli", {}).get(
        "uname", "FlaskOS 1.0 Kernel v4.2 web-based x86_64"
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
    host_template = neofetch_config.get("host_template", "{name}'s Dev Environment")

    logo = []
    try:
        logo_path = _get_data_filepath("logo/neofetch_logo_flask.txt")
        with open(logo_path, "r", encoding="utf-8") as f:
            logo = [line.rstrip() for line in f.readlines()]
    except FileNotFoundError:
        logo = [t("cli_out.logo_not_found")]

    info = [
        f"{name}@{text_config.get('cli', {}).get('prompt', {}).get('host', 'flaskos')}",
        "-----------------------",
        f"OS: {neofetch_config.get('os_name', 'FlaskOS 1.0')}",
        f"Host: {host_template.format(name=name)}",
        f"{t('cli_out.neofetch_title')}: {title}",
        f"{t('cli_out.neofetch_projects')}: {project_count}",
        f"{t('cli_out.neofetch_skills')}: {skill_count}",
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
        return None, t("cli_out.man_usage")

    command_name = args[0].lower()
    if command_name in ("exit", "close"):
        command_name = "exit"

    manuals = text_config.get("cli", {}).get("manuals", {})
    manual_text = manuals.get(command_name)
    if not manual_text:
        return None, t("cli_out.man_none", command=command_name)
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
            jsonify({"output": [], "error": t("cli_out.load_failed")}),
            500,
        )

    # Sanitize to prevent Werkzeug 404 on trailing slash
    if command_line.endswith("/"):
        command_line = command_line[:-1]

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
            error = t("cli_out.command_not_found", command=command)

    except Exception as e:
        logger.error(
            f"CLI API exception processing command '{command_line}': {e}",
            exc_info=True,
        )
        error = t("cli_out.internal_error")

    response_data = {"output": output or [], "error": error, "command": command}
    if action:
        response_data.update(action)

    prompt_config = TEXT_CONFIG.get("cli", {}).get("prompt", {})
    response_data["prompt"] = prompt_config

    return jsonify(response_data)
