import copy
import logging
import os
import re

from flask import abort, jsonify, send_from_directory

from common.utils import load_cv_data, load_projects_data, load_recruiter_story_data

from . import recruiter_bp

logger = logging.getLogger(__name__)


# --- Helper function to replace placeholders in text ---
def _replace_placeholders(text, cv_data, projects_dict):
    """Replaces placeholders like {{ cv.name }} or {{ desc_project-id }} in text."""
    if not text:
        return ""

    # Replace CV placeholders like {{ cv.name }} or {{ cv.skills_list }}
    def replace_cv(match):
        key = match.group(1).strip()  # e.g., 'name' or 'skills'
        value = cv_data.get(key, f"{{cv.{key}_not_found}}")
        if isinstance(value, list):
            # Simple list join for skills etc. Adjust formatting if needed.
            return ", ".join(value) if value else "(None listed)"
        return str(value)

    text = re.sub(r"{{\s*cv\.(\w+)\s*}}", replace_cv, text)

    # Replace project description placeholders like {{ desc_project-id }}
    def replace_proj_desc(match):
        proj_id = match.group(1).strip()
        project = projects_dict.get(proj_id)
        return (
            project.get("description", f"{{desc_{proj_id}_not_found}}")
            if project
            else f"{{desc_{proj_id}_not_found}}"
        )

    text = re.sub(r"{{\s*desc_([\w-]+)\s*}}", replace_proj_desc, text)

    # --- Add more complex placeholder replacements ---
    if "{{ core_backend_skills }}" in text:
        backend_keywords = [
            "python",
            "flask",
            "fastapi",
            "api",
            "sql",
            "sqlalchemy",
            "postgresql",
            "docker",
            "linux",
        ]
        skills = [
            s
            for s in cv_data.get("skills", [])
            if any(k in s.lower() for k in backend_keywords)
        ]
        text = text.replace(
            "{{ core_backend_skills }}",
            ", ".join(skills) if skills else "Python, Web Frameworks, Databases",
        )

    if "{{ core_frontend_skills }}" in text:
        frontend_keywords = [
            "html",
            "css",
            "javascript",
            "tailwind",
            "bootstrap",
            "svg",
        ]
        skills = [
            s
            for s in cv_data.get("skills", [])
            if any(k in s.lower() for k in frontend_keywords)
        ]
        text = text.replace(
            "{{ core_frontend_skills }}",
            ", ".join(skills) if skills else "HTML, CSS, JavaScript",
        )

    if "{{ core_database_skills }}" in text:
        db_keywords = ["sql", "sqlalchemy", "postgresql", "sqlite", "redis"]
        skills = [
            s
            for s in cv_data.get("skills", [])
            if any(k in s.lower() for k in db_keywords)
        ]
        text = text.replace(
            "{{ core_database_skills }}",
            ", ".join(skills) if skills else "SQLAlchemy, PostgreSQL, SQLite",
        )

    if "{{ core_tools }}" in text:
        tool_keywords = ["git", "docker", "n8n", "linux", "api", "pytest", "pypi"]
        skills = [
            s
            for s in cv_data.get("skills", [])
            if any(k in s.lower() for k in tool_keywords)
        ]
        text = text.replace(
            "{{ core_tools }}",
            ", ".join(skills) if skills else "Git, Docker, Automation Tools",
        )

    # TODO: Add logic for project lists like {{ project_list_web }}
    if "{{ project_list_web }}" in text:
        # Iterate over values() if you only need 'p'
        web_projects = [p for p in projects_dict.values() if p.get("type") == "webapp"]
        proj_list_str = (
            "\n".join([f"    * {p.get('title', p.get('id'))}" for p in web_projects])
            if web_projects
            else "    (No specific web apps listed)"
        )
        text = text.replace("{{ project_list_web }}", proj_list_str)

    if "{{ project_list_automation }}" in text:
        auto_keywords = ["automateiq", "automation", "api", "n8n", "connector"]
        # Iterate over values() if you only need 'p'
        auto_projects = [
            p
            for p in projects_dict.values()
            if any(k in p.get("id", "").lower() for k in auto_keywords)
            or any(k in p.get("title", "").lower() for k in auto_keywords)
        ]  # Check 'id' on p
        proj_list_str = (
            "\n".join([f"    * {p.get('title', p.get('id'))}" for p in auto_projects])
            if auto_projects
            else "    (No specific automation/API projects listed)"
        )
        text = text.replace("{{ project_list_automation }}", proj_list_str)

    return text


# --- Helper function to handle dynamic steps ---
def _get_dynamic_step_data(step_id, cv_data, projects_data, projects_dict, story_data):
    """Generates step data for dynamic steps like project details or tags."""
    logger.debug(f"Handling dynamic step request: {step_id}")

    if step_id.startswith("project_detail_"):
        project_id = step_id.replace("project_detail_", "")
        project = projects_dict.get(project_id)
        if project:
            # Construct text and choices for a project detail view
            # Using Markdown-like syntax for JS to potentially parse
            text = f"**{project.get('title', 'Project Detail')}**\n\n"
            text += f"*Type:* {project.get('type', 'N/A').capitalize()}\n\n"
            text += f"*Description:* {project.get('description', 'N/A')}\n\n"
            if project.get("technologies"):
                text += (
                    f"*Technologies:* {', '.join(project.get('technologies', []))}\n"
                )

            choices = []
            # Add relevant links as choices with 'url' type
            if project.get("live_url"):
                choices.append(
                    {
                        "text": f"View Live Demo ({project_id})",
                        "url": project["live_url"],
                    }
                )
            if project.get("github_url"):
                choices.append(
                    {"text": f"View Code ({project_id})", "url": project["github_url"]}
                )
            if project.get("pypi_url"):
                choices.append(
                    {"text": f"View on PyPI ({project_id})", "url": project["pypi_url"]}
                )
            if project.get("docs_url"):
                choices.append(
                    {"text": f"View Docs ({project_id})", "url": project["docs_url"]}
                )

            # Add navigation choices
            choices.append(
                {
                    "text": "Explore other web projects.",
                    "next_step": "web_apps_overview",
                }
            )
            choices.append(
                {
                    "text": "Explore automation/API projects.",
                    "next_step": "automation_apis_overview",
                }
            )
            choices.append({"text": "Back to start.", "next_step": "start"})

            # Replace placeholders within the dynamically generated text as well
            final_text = _replace_placeholders(text, cv_data, projects_dict)
            return {"step_id": step_id, "text": final_text, "choices": choices}
        else:
            logger.warning(f"Project ID not found for dynamic step: {project_id}")
            # Return the 'step_not_found' structure from story data
            not_found_step = story_data.get(
                "step_not_found", {"text": "Error: Project not found.", "choices": []}
            )
            not_found_step["step_id"] = step_id  # Reflect requested step in response
            return not_found_step

    elif step_id.startswith("project_tag_"):
        tag = step_id.replace(
            "project_tag_", ""
        ).lower()  # Ensure tag is lowercase for comparison
        # Find projects matching the tag (simple lowercase keyword check in technologies list)
        matching_projects = [
            p
            for p_id, p in projects_dict.items()
            if tag in [tech.lower() for tech in p.get("technologies", [])]
        ]
        if matching_projects:
            text = f"Here are projects related to **{tag.capitalize()}**:\n\n"
            choices = []
            for p in matching_projects:
                # Using project ID in description text for clarity
                short_desc = (
                    p.get(
                        "short_description",
                        p.get("description", "No description available."),
                    )[:80]
                    + "..."
                )
                text += f"*   **{p.get('title', p.get('id'))}**: {short_desc}\n"
                choices.append(
                    {
                        "text": f"Details on: {p.get('title', p.get('id'))}.",
                        "next_step": f"project_detail_{p.get('id')}",
                    }
                )

            # Add navigation choices
            choices.append(
                {"text": "Explore core skills again.", "next_step": "core_skills"}
            )
            choices.append({"text": "Back to start.", "next_step": "start"})
            # Replace placeholders in dynamically generated text
            final_text = _replace_placeholders(text, cv_data, projects_dict)
            return {"step_id": step_id, "text": final_text, "choices": choices}
        else:
            logger.warning(f"No projects found for dynamic tag step: {tag}")
            # Go back to skills overview, prepending a message
            step_data = copy.deepcopy(
                story_data.get("core_skills", {})
            )  # Deep copy to avoid modifying cache
            original_text = step_data.get("text", "")
            step_data["text"] = (
                f"Sorry, I couldn't find specific projects tagged with '{tag}'.\n\n"
                + original_text
            )
            step_data["step_id"] = step_id  # Reflect requested step
            # Replace placeholders in this fallback text too
            step_data["text"] = _replace_placeholders(
                step_data["text"], cv_data, projects_dict
            )
            return step_data

    # Add more dynamic step handlers here... e.g., specific skill deep dives

    logger.warning(f"Unhandled dynamic step ID pattern: {step_id}")
    return None  # Indicate dynamic handler didn't match


# --- Route to serve static files for this blueprint ---
@recruiter_bp.route("/static/<path:filename>")
def static_files(filename):
    """Serves static files specific to the Recruiter blueprint."""
    # Construct path relative to the blueprint's root path
    static_dir = os.path.join(recruiter_bp.root_path, "static")
    logger.debug(f"Serving Recruiter static file: {filename} from {static_dir}")
    # Use try-except for robustness
    try:
        return send_from_directory(static_dir, filename)
    except FileNotFoundError:
        logger.error(f"Static file not found: {os.path.join(static_dir, filename)}")
        abort(404)


# --- API Endpoint ---
@recruiter_bp.route("/api/step/<step_id>")
def get_step_data_api(step_id):
    """Gets the data for a specific step in the recruiter story."""
    logger.info(f"Recruiter API requested step: {step_id}")

    # Load necessary data using Flask 'g' for caching per request
    story_data = load_recruiter_story_data()
    cv_data = load_cv_data()
    projects_data, projects_dict = load_projects_data()

    # Ensure data loaded correctly
    if (
        not story_data or not cv_data or projects_data is None
    ):  # projects_data can be empty list
        logger.error("Failed to load necessary data (Story, CV, or Projects).")
        return jsonify({"error": "Failed to load backend data."}), 500

    step_content = None

    # 1. Check if it's a dynamically handled step
    dynamic_content = _get_dynamic_step_data(
        step_id, cv_data, projects_data, projects_dict, story_data
    )
    if dynamic_content:
        step_content = dynamic_content
    else:
        # 2. If not dynamic, look for it directly in the story YAML
        step_content = story_data.get(step_id)

    # 3. If still not found, use the 'step_not_found' step from YAML
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
        step_content["step_id"] = step_id  # Reflect requested step in response

    # Make a deep copy to avoid modifying the cached data in 'g'
    response_data = copy.deepcopy(step_content)

    # Replace placeholders in the final text before sending
    if "text" in response_data:
        response_data["text"] = _replace_placeholders(
            response_data["text"], cv_data, projects_dict
        )

    # Optionally replace placeholders in choice text too (if needed)
    if "choices" in response_data:
        for choice in response_data["choices"]:
            if "text" in choice:
                choice["text"] = _replace_placeholders(
                    choice["text"], cv_data, projects_dict
                )

    return jsonify(response_data)
