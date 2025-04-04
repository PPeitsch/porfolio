from flask import jsonify, current_app, g
from . import cli_bp
from common.utils import load_cv_data, load_projects_data
import logging

logger = logging.getLogger(__name__)


# --- Helper to get cached data within the context of this blueprint ---
def get_cached_data(data_type='cv'):
    """Helper to load data once per app context for CLI."""
    if data_type == 'cv':
        if 'cv_data' not in g:
            g.cv_data = load_cv_data()
            logger.info("CLI: CV data loaded into context g")
        return g.cv_data
    elif data_type == 'projects':
        if 'projects_data' not in g:
            g.projects_data, g.projects_dict = load_projects_data()
            logger.info("CLI: Projects data loaded into context g")

        if 'projects_dict' not in g and 'projects_data' in g:
            g.projects_dict = {p.get('id', f'proj_{i}'): p for i, p in
                               enumerate(g.projects_data)} if g.projects_data else {}
        return g.projects_data, g.projects_dict
    return None


# --- API Endpoint for CLI Commands ---
@cli_bp.route('/api/command/<path:command_line>')
def handle_command_api(command_line):
    """Processes a 'command' from the JS terminal via API."""
    logger.debug(f"CLI API received command: {command_line}")
    CV_DATA = get_cached_data('cv')
    PROJECTS_DATA, PROJECTS_DICT = get_cached_data('projects')

    parts = command_line.lower().strip().split()
    command = parts[0] if parts else ''
    args = parts[1:]

    output = []
    error = None

    try:
        # --- Basic Command Processing Logic (Expand Later) ---
        if command == 'help':
            output.append("Available commands:")
            output.append("  help           - Show this help message")
            output.append("  whoami         - Display summary about me")
            output.append("  ls projects    - List available projects")
            output.append("  show <project> - Show project details (use ID from 'ls projects')")
            output.append("  clear          - Clear the terminal screen")
            # Add more commands later (skills, links, contact)
        elif command == 'whoami':
            # Placeholder - load actual data in next step
            output.append(f"Name: {CV_DATA.get('name', 'Loading...')}")
            output.append(f"Title: {CV_DATA.get('title', 'Loading...')}")
            output.append("---")
            output.append("Summary will be loaded here.")
        elif command == 'ls' and args and args[0] == 'projects':
            output.append("Projects (use 'show <id>' for details):")
            if PROJECTS_DATA:
                # Basic list - formatting later
                for p in PROJECTS_DATA:
                    output.append(f"  - {p.get('id', 'N/A')} : {p.get('title', 'N/A')}")
            else:
                output.append("  (No projects loaded or found)")
        elif command == 'show' and args:
            project_id = args[0]
            project = PROJECTS_DICT.get(project_id) if PROJECTS_DICT else None
            if project:
                output.append(f"--- Project: {project.get('title', 'Loading...')} ---")
                output.append(f"Description: {project.get('description', 'Loading...')}")
                # Add tech/links later
            else:
                error = f"Error: Project '{project_id}' not found."
        elif command == 'clear':
            pass  # Handled only by JS frontend
        elif command == '':
            pass  # Ignore empty command
        else:
            error = f"Error: Command not found '{command}'. Type 'help' for available commands."
        # --- End Basic Command Logic ---

    except Exception as e:
        logger.error(f"CLI API error processing command '{command_line}': {e}", exc_info=True)
        error = "An internal server error occurred processing the command."

    return jsonify({'output': output, 'error': error, 'command': command})
