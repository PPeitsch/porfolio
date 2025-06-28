from typing import Any, Callable, Dict, List

from app.common import utils

# A mapping from tool name to the actual callable function.
TOOL_MAP: Dict[str, Callable[..., Any]] = {
    "get_professional_summary": utils.get_professional_summary,
    "get_skills": utils.get_skills,
    "get_project_list": utils.get_project_list,
    "get_project_details": utils.get_project_details,
}


def get_tool_definitions(owner_name: str) -> List[Dict[str, Any]]:
    """
    Generates the list of tool definitions for the LLM, populating
    descriptions with the portfolio owner's name.

    Args:
        owner_name: The name of the portfolio owner to insert into descriptions.

    Returns:
        A list of tool definition dictionaries.
    """
    text_config = utils.load_text_config()
    descriptions = text_config.get("llm_tool_descriptions", {})

    tool_definitions = [
        {
            "name": "get_professional_summary",
            "description": descriptions.get(
                "get_professional_summary",
                "Retrieves the professional summary of the portfolio owner.",
            ).format(name=owner_name),
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "get_skills",
            "description": descriptions.get(
                "get_skills", "Retrieves a list of the portfolio owner's skills."
            ).format(name=owner_name),
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": (
                            "Optional category to filter skills (e.g., 'backend', "
                            "'frontend'). Currently not implemented."
                        ),
                    }
                },
            },
        },
        {
            "name": "get_project_list",
            "description": descriptions.get(
                "get_project_list", "Retrieves a summary list of all projects."
            ).format(name=owner_name),
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "get_project_details",
            "description": descriptions.get(
                "get_project_details",
                "Retrieve detailed information for a specific project.",
            ).format(name=owner_name),
            "input_schema": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": (
                            "The unique identifier for the project, e.g., "
                            "'portfolio', 'automateiq'."
                        ),
                    }
                },
                "required": ["project_id"],
            },
        },
    ]
    return tool_definitions
