from typing import Any, Callable, Dict, List

from common import utils

# A mapping from tool name to the actual callable function.
# This allows the chat handler to dynamically execute the correct function
# based on the name provided by the LLM.
TOOL_MAP: Dict[str, Callable[..., Any]] = {
    "get_professional_summary": utils.get_professional_summary,
    "get_skills": utils.get_skills,
    "get_project_list": utils.get_project_list,
    "get_project_details": utils.get_project_details,
}

# A list of tool definitions formatted for the LLM.
# Each dictionary describes a tool's name, purpose, and input schema.
# This structured information enables the LLM to decide when to use a tool
# and what arguments to provide.
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "get_professional_summary",
        "description": (
            "Retrieves the professional summary or overview of Pablo Peitsch. "
            "Use this to answer general questions about his background and focus."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_skills",
        "description": (
            "Retrieves a list of Pablo Peitsch's technical skills. Use this to "
            "answer questions about his expertise in specific technologies, "
            "languages, or frameworks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": (
                        "Optional category to filter skills (e.g., 'backend', "
                        "'frontend'). Currently not implemented, but reserved "
                        "for future use."
                    ),
                }
            },
        },
    },
    {
        "name": "get_project_list",
        "description": (
            "Retrieves a summary list of all available projects. Use this when "
            "the user asks for an overview of projects or wants to know what "
            "projects exist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_project_details",
        "description": (
            "Retrieve detailed information for a specific project based on its "
            "unique identifier (ID). Use this when the user asks for details "
            "about a specific project by name or ID."
        ),
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
