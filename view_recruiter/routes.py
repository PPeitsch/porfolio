import copy
import logging
import os
import re

from flask import abort, jsonify, send_from_directory

from common.utils import load_cv_data, load_projects_data, load_recruiter_story_data

from . import recruiter_bp

logger = logging.getLogger(__name__)


def _replace_placeholders(text, cv_data, projects_dict):
    """Replaces various placeholders in story text with dynamic data.

    This function is responsible for populating templates within the story YAML.
    It handles placeholders for CV details (e.g., {{ cv.name }}), project
    descriptions (e.g., {{ desc_project-id }}), and dynamically generated
    lists of skills or projects.

    Args:
        text (str): The string containing placeholders.
        cv_data (dict): The loaded CV data dictionary.
        projects_dict (dict): The loaded projects data, keyed by ID.

    Returns:
        str: The text with all placeholders replaced with their corresponding data.
    """
    if not text or not isinstance(text, str):
        return ""

    def replace_cv(match):
        key = match.group(1).strip()
        value = cv_data.get(key, f"{{cv.{key}_not_found}}")
        if isinstance(value, list):
            return ", ".join(value) if value else "(None listed)"
        return str(value)

    text = re.sub(r"{{\s*cv\.(\w+?)\s*}}", replace_cv, text)

    def replace_proj_desc(match):
        proj_id = match.group(1).strip()
        project = projects_dict.get(proj_id)
        desc = (
            project.get(
                "short_description",
                project.get("description", f"{{desc_{proj_id}_not_found}}"),
            )
            if project
            else f"{{desc_{proj_id}_not_found}}"
        )
        return desc

    text = re.sub(r"{{\s*desc_([\w-]+?)\s*}}", replace_proj_desc, text)

    def replace_skill_list(match):
        skill_type = match.group(1).strip()
        skills_list = cv_data.get("skills", [])
        keywords = []
        default_text = "(Details not specified)"

        if skill_type == "core_backend_skills":
            keywords = [
                "python",
                "flask",
                "fastapi",
                "api",
                "sql",
                "sqlalchemy",
                "postgresql",
                "docker",
                "linux",
                "backend",
            ]
            default_text = (
                "Python, Web Frameworks (Flask/FastAPI), Databases, APIs, Docker"
            )
        elif skill_type == "core_frontend_skills":
            keywords = [
                "html",
                "css",
                "javascript",
                "tailwind",
                "bootstrap",
                "svg",
                "frontend",
            ]
            default_text = (
                "HTML, CSS, JavaScript (including frameworks like Tailwind/Bootstrap)"
            )
        elif skill_type == "core_database_skills":
            db_keywords = [
                "sql",
                "sqlalchemy",
                "postgresql",
                "sqlite",
                "redis",
                "database",
            ]
            skills = [
                s for s in skills_list if any(k in s.lower() for k in db_keywords)
            ]
            if skills:
                return ", ".join(skills)
            else:
                return "Experience with relational (PostgreSQL, SQLite) and non-relational databases"
        elif skill_type == "core_tools":
            keywords = [
                "git",
                "docker",
                "n8n",
                "linux",
                "api",
                "pytest",
                "pypi",
                "ci/cd",
                "pre-commit",
                "cli",
                "testing",
                "deployment",
            ]
            default_text = "Git, Docker, CI/CD, Testing Frameworks, Linux Environment"
        elif skill_type == "testing_tools":
            keywords = ["pytest", "unittest", "selenium", "playwright", "coverage"]
            default_text = "Pytest (Unit/Integration), Coverage Analysis"

        if keywords:
            matched_skills = [
                s for s in skills_list if any(k in s.lower() for k in keywords)
            ]
            return ", ".join(matched_skills) if matched_skills else default_text
        else:
            return default_text

    text = re.sub(r"{{\s*([\w_]+?)\s*}}", replace_skill_list, text)

    def replace_project_list(match):
        list_type = match.group(1).strip()
        all_projects = list(projects_dict.values()) if projects_dict else []
        projects_to_list = []
        default_text = "\n    (No specific projects found for this category)"

        if list_type == "project_list_web":
            projects_to_list = [p for p in all_projects if p.get("type") == "webapp"]
            default_text = "\n    (No specific web apps listed in projects.yaml)"
        elif list_type == "project_list_automation":
            auto_keywords = [
                "automateiq",
                "automation",
                "api",
                "n8n",
                "connector",
                "bcra-connector",
            ]
            projects_to_list = [
                p
                for p in all_projects
                if any(k in p.get("id", "").lower() for k in auto_keywords)
                or any(k in p.get("title", "").lower() for k in auto_keywords)
                or "api client" in p.get("description", "").lower()
                or p.get("type") == "library"
            ]
            default_text = "\n    (No specific automation/API projects found)"
        elif list_type == "project_list_library":
            projects_to_list = [p for p in all_projects if p.get("type") == "library"]
            default_text = "\n    (No specific libraries listed)"
        elif list_type == "project_list_data":
            projects_to_list = [
                p
                for p in all_projects
                if p.get("type") == "repo" or "analysis" in p.get("title", "").lower()
            ]
            default_text = "\n    (No specific data analysis projects/repos listed)"

        if projects_to_list:
            proj_list_items = [
                f"    *   **{p.get('title', p.get('id'))}** (ID: `{p.get('id')}`)"
                for p in projects_to_list
            ]
            return "\n" + "\n".join(proj_list_items)
        else:
            return default_text

    text = re.sub(r"{{\s*(project_list_\w+?)\s*}}", replace_project_list, text)

    return text


def _get_dynamic_step_data(step_id, cv_data, projects_data, projects_dict, story_data):
    """Generates story step data for dynamic IDs (e.g., project details).

    This function handles step IDs that are not explicitly defined in the
    story YAML, such as 'project_detail_*' or 'project_tag_*'. It builds
    the step's text and choices dynamically based on project data.

    Args:
        step_id (str): The requested step ID.
        cv_data (dict): The loaded CV data.
        projects_data (list): The list of project dicts.
        projects_dict (dict): The dict of projects keyed by ID.
        story_data (dict): The full story structure from YAML.

    Returns:
        dict | None: A dictionary for the generated step, or None if the
                     step_id pattern doesn't match a dynamic handler.
    """
    logger.debug(f"Handling dynamic step request: {step_id}")
    step_data = None

    if step_id.startswith("project_detail_"):
        project_id = step_id.replace("project_detail_", "")
        project = projects_dict.get(project_id)
        if project:
            text = f"### {project.get('title', 'Project Detail')}\n\n"
            text += f"**Type:** {project.get('type', 'N/A').capitalize()}\n\n"
            full_desc = project.get("description", "N/A")
            import textwrap

            wrapped_desc = textwrap.wrap(
                full_desc, width=70, initial_indent="  ", subsequent_indent="  "
            )
            text += f"**Description:**\n{'<br>'.join(wrapped_desc)}\n\n"
            if project.get("technologies"):
                tech_tags = " ".join(
                    [f"`{t}`" for t in project.get("technologies", [])]
                )
                text += f"**Technologies:** {tech_tags}\n"

            choices = []
            if project.get("live_url"):
                choices.append(
                    {"text": "🔗 View Live Demo", "url": project["live_url"]}
                )
            if project.get("github_url"):
                choices.append(
                    {"text": "🔗 View Code (GitHub)", "url": project["github_url"]}
                )
            if project.get("pypi_url"):
                choices.append({"text": "🔗 View on PyPI", "url": project["pypi_url"]})
            if project.get("docs_url"):
                choices.append({"text": "🔗 View Docs", "url": project["docs_url"]})
            if project.get("type") == "webapp":
                choices.append(
                    {"text": "‹ Other Web Projects", "next_step": "web_apps_overview"}
                )
            elif project.get("type") == "library":
                choices.append(
                    {"text": "‹ Other Libraries", "next_step": "library_overview"}
                )
            elif project.get("type") == "repo":
                choices.append(
                    {
                        "text": "‹ Other Data/Repo Work",
                        "next_step": "data_analysis_overview",
                    }
                )
            choices.append(
                {
                    "text": "« See All Project Types",
                    "next_step": "project_type_overview",
                }
            )
            choices.append({"text": "« Back to Start", "next_step": "start"})
            step_data = {"step_id": step_id, "text": text, "choices": choices}
        else:
            logger.warning(f"Project ID not found for dynamic step: {project_id}")
            step_data = story_data.get(
                "step_not_found", {"text": "Error: Project not found.", "choices": []}
            )
            step_data["step_id"] = step_id

    elif step_id.startswith("project_tag_"):
        tag = step_id.replace("project_tag_", "").lower()
        matching_projects = [
            p
            for p in projects_dict.values()
            if tag in [tech.lower() for tech in p.get("technologies", [])]
        ]
        if matching_projects:
            text = f"### Projects using {tag.capitalize()}\n\n"
            choices = []
            for p in matching_projects:
                short_desc = (
                    p.get("short_description", p.get("description", ""))[:80] + "..."
                )
                text += f"*   **{p.get('title', p.get('id'))}**: {short_desc}\n"
                choices.append(
                    {
                        "text": f"Details on: {p.get('title', p.get('id'))}",
                        "next_step": f"project_detail_{p.get('id')}",
                    }
                )
            choices.append(
                {"text": "‹ Explore Core Skills", "next_step": "core_skills"}
            )
            choices.append({"text": "« Back to Start", "next_step": "start"})
            step_data = {"step_id": step_id, "text": text, "choices": choices}
        else:
            logger.warning(f"No projects found for dynamic tag step: {tag}")
            step_data = copy.deepcopy(story_data.get("core_skills", {}))
            original_text = step_data.get("text", "")
            step_data["text"] = (
                f"_(Sorry, I couldn't find specific projects tagged with '{tag}' in their technologies list.)_\n\n"
                + original_text
            )
            step_data["step_id"] = step_id

    elif step_id.startswith("project_docs_"):
        project_id = step_id.replace("project_docs_", "")
        project = projects_dict.get(project_id)
        if project and project.get("docs_url"):
            text = (
                f"The documentation for **{project.get('title')}** is available online."
            )
            choices = [
                {"text": "🔗 Open Documentation", "url": project["docs_url"]},
                {
                    "text": f"‹ More details about {project.get('title')}",
                    "next_step": f"project_detail_{project_id}",
                },
                {"text": "‹ Explore other libraries", "next_step": "library_overview"},
                {"text": "« Back to start", "next_step": "start"},
            ]
            step_data = {"step_id": step_id, "text": text, "choices": choices}
        else:
            logger.warning(f"Docs URL not found for project: {project_id}")
            step_data = _get_dynamic_step_data(
                f"project_detail_{project_id}",
                cv_data,
                projects_data,
                projects_dict,
                story_data,
            )
            if step_data:
                step_data["text"] = (
                    f"_(Note: Specific documentation link not found for {project.get('title', project_id)}.)_\n\n"
                    + step_data["text"]
                )
            else:
                step_data = story_data.get(
                    "step_not_found",
                    {"text": "Error: Project details not found.", "choices": []},
                )
                step_data["step_id"] = step_id

    if step_data and "text" in step_data:
        step_data["text"] = _replace_placeholders(
            step_data["text"], cv_data, projects_dict
        )

    return step_data


@recruiter_bp.route("/static/<path:filename>")
def static_files(filename):
    """Serves static files specific to the Recruiter blueprint.

    Args:
        filename (str): The name of the file to serve from the static folder.

    Returns:
        Response: The requested static file or a 404 error if not found.
    """
    static_dir = os.path.join(recruiter_bp.root_path, "static")
    logger.debug(f"Serving Recruiter static file: {filename} from {static_dir}")
    try:
        return send_from_directory(static_dir, filename)
    except FileNotFoundError:
        logger.error(f"Static file not found: {os.path.join(static_dir, filename)}")
        abort(404)


@recruiter_bp.route("/api/step/<step_id>")
def get_step_data_api(step_id):
    """API endpoint to get data for a specific story step.

    It orchestrates fetching the correct step from either the static story
    YAML or by generating it dynamically. It then replaces placeholders
    in the text and returns the final content as JSON.

    Args:
        step_id (str): The ID of the story step to retrieve.

    Returns:
        Response: A JSON response containing the step's 'text', 'choices',
                  and 'step_id'.
    """
    logger.info(f"Recruiter API requested step: {step_id}")

    story_data = load_recruiter_story_data()
    cv_data = load_cv_data()
    projects_data, projects_dict = load_projects_data()

    if not story_data or not cv_data or projects_data is None or projects_dict is None:
        logger.error("Failed to load necessary data (Story, CV, or Projects).")
        return (
            jsonify(
                {"error": "Failed to load backend data. Please check server logs."}
            ),
            500,
        )

    step_content = _get_dynamic_step_data(
        step_id, cv_data, projects_data, projects_dict, story_data
    )
    if not step_content:
        step_content = story_data.get(step_id)
    if not step_content:
        logger.warning(
            f"Step ID '{step_id}' not found in story YAML or dynamic handlers."
        )
        step_content = story_data.get(
            "step_not_found",
            {
                "text": "Error: Step not found.",
                "choices": [{"text": "Start Over", "next_step": "start"}],
            },
        )
        step_content["step_id"] = step_id

    response_data = copy.deepcopy(step_content)

    if "text" in response_data:
        response_data["text"] = _replace_placeholders(
            response_data["text"], cv_data, projects_dict
        )
    if "choices" in response_data:
        for choice in response_data["choices"]:
            if "text" in choice:
                choice["text"] = _replace_placeholders(
                    choice["text"], cv_data, projects_dict
                )

    return jsonify(response_data)
