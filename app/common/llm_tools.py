from typing import Any, Callable, Dict, List

from app.common import utils

# A mapping from tool name to the actual callable function.
TOOL_MAP: Dict[str, Callable[..., Any]] = {
    "get_professional_summary": utils.get_professional_summary,
    "get_skills": utils.get_skills,
    "get_experience": utils.get_experience,
    "get_education": utils.get_education,
    "get_project_list": utils.get_project_list,
    "get_project_details": utils.get_project_details,
}


def get_tool_definitions(owner_name: str) -> List[Dict[str, Any]]:
    """
    Generates the list of tool definitions for the LLM, in OpenAI format,
    populating descriptions with the portfolio owner's name.

    Args:
        owner_name: The name of the portfolio owner to insert into descriptions.

    Returns:
        A list of tool definition dictionaries.
    """
    text_config = utils.load_text_config()
    descriptions = text_config.get("llm_tool_descriptions", {})

    def describe(tool: str, default: str) -> str:
        return str(descriptions.get(tool, default)).replace("{name}", owner_name)

    def tool(name: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }

    no_parameters: Dict[str, Any] = {"type": "object", "properties": {}}
    tool_definitions = [
        tool(
            "get_professional_summary",
            describe(
                "get_professional_summary",
                "Retrieves the professional summary of the portfolio owner.",
            ),
            no_parameters,
        ),
        tool(
            "get_skills",
            describe("get_skills", "Retrieves a list of the portfolio owner's skills."),
            {
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
        ),
        tool(
            "get_experience",
            describe(
                "get_experience",
                "Retrieves the portfolio owner's work experience: role, company, "
                "period and description of each position.",
            ),
            no_parameters,
        ),
        tool(
            "get_education",
            describe(
                "get_education",
                "Retrieves the portfolio owner's education: degree, institution "
                "and period of each entry.",
            ),
            no_parameters,
        ),
        tool(
            "get_project_list",
            describe("get_project_list", "Retrieves a summary list of all projects."),
            no_parameters,
        ),
        tool(
            "get_project_details",
            describe(
                "get_project_details",
                (
                    "Retrieve detailed information for a specific project. "
                    "If the project ID is not found, it returns an error message."
                ),
            ),
            {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": (
                            "The unique identifier for the project, as returned "
                            "by get_project_list."
                        ),
                    }
                },
                "required": ["project_id"],
            },
        ),
    ]
    return tool_definitions
