from flask import jsonify, current_app, g, abort
from . import recruiter_bp
from common.utils import (
    load_cv_data,
    load_projects_data,
    load_recruiter_story_data,
)
import logging
import re

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
            return ", ".join(value)  # Simple list join for skills etc.
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
    # Example: {{ core_backend_skills }} - requires logic
    if "{{ core_backend_skills }}" in text:
        # Define which skills are core backend (example logic)
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

    # Add similar replacements for frontend, database, tools, project lists etc.
    # Example for {{ core_frontend_skills }}
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

    # TODO: Add logic for {{ project_list_web }}, {{ project_list_automation }} etc.

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
            text = f"**{project.get('title', 'Project Detail')}**\n\n"  # Use markdown? JS needs to parse.
            text += f"Type: {project.get('type', '').capitalize()}\n"
            text += f"Description: {project.get('description', 'N/A')}\n"
            if project.get("technologies"):
                text += f"Technologies: {', '.join(project.get('technologies',[]))}\n"

            choices = []
            if project.get("live_url"):
                choices.append(
                    {
                        "text": f"View Live Demo ({project_id})",
                        "url": project["live_url"],
                    }
                )  # Add URL type choice
            if project.get("github_url"):
                choices.append(
                    {
                        "text": f"View Code on GitHub ({project_id})",
                        "url": project["github_url"],
                    }
                )
            if project.get("pypi_url"):
                choices.append(
                    {"text": f"View on PyPI ({project_id})", "url": project["pypi_url"]}
                )
            if project.get("docs_url"):
                choices.append(
                    {
                        "text": f"View Documentation ({project_id})",
                        "url": project["docs_url"],
                    }
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

            return {"step_id": step_id, "text": text, "choices": choices}
        else:
            logger.warning(f"Project ID not found for dynamic step: {project_id}")
            return story_data.get(
                "step_not_found", {"text": "Error: Project not found.", "choices": []}
            )

    elif step_id.startswith("project_tag_"):
        tag = step_id.replace("project_tag_", "")
        # Find projects matching the tag (simple lowercase keyword check)
        matching_projects = [
            p
            for p in projects_data
            if tag in [tech.lower() for tech in p.get("technologies", [])]
        ]
        if matching_projects:
            text = f"Here are projects related to **{tag.capitalize()}**:\n\n"
            choices = []
            for p in matching_projects:
                text += f"*   **{p.get('title')}**: {p.get('short_description', p.get('description', ''))[:60]}...\n"  # Show short desc
                choices.append(
                    {
                        "text": f"Tell me more about {p.get('title')}.",
                        "next_step": f"project_detail_{p.get('id')}",
                    }
                )

            choices.append(
                {"text": "Explore core skills again.", "next_step": "core_skills"}
            )
            choices.append({"text": "Back to start.", "next_step": "start"})
            return {"step_id": step_id, "text": text, "choices": choices}
        else:
            logger.warning(f"No projects found for dynamic tag step: {tag}")
            # Go back to skills overview or provide other options
            step_data = story_data.get("core_skills", {}).copy()  # Get base skills step
            step_data["text"] = (
                f"Sorry, I couldn't find specific projects tagged with '{tag}'.\n\n"
                + step_data.get("text", "")
            )  # Prepend message
            return step_data
            # return story_data.get('step_not_found', {'text': f'Error: No projects found for tag "{tag}".', 'choices': []})

    # Add more dynamic step handlers here...

    logger.warning(f"Unhandled dynamic step ID pattern: {step_id}")
    return None  # Indicate dynamic handler didn't match


# --- API Endpoint ---
@recruiter_bp.route("/api/step/<step_id>")
def get_step_data_api(step_id):
    """Gets the data for a specific step in the recruiter story."""
    logger.info(f"Recruiter API requested step: {step_id}")

    # Load necessary data
    story_data = load_recruiter_story_data()
    cv_data = load_cv_data()
    projects_data, projects_dict = load_projects_data()

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
        # Ensure the step_id in the response reflects what was requested, even for errors
        step_content["step_id"] = (
            step_id  # Or maybe 'step_not_found'? Decide on desired behavior.
        )

    # Make a deep copy to avoid modifying the cached data
    import copy

    response_data = copy.deepcopy(step_content)

    # Replace placeholders in the text before sending
    if "text" in response_data:
        response_data["text"] = _replace_placeholders(
            response_data["text"], cv_data, projects_dict
        )

    # Format choices if needed (e.g., replace placeholders in choice text) - currently not implemented

    return jsonify(response_data)
