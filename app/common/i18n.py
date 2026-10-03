"""Language selection and bilingual content.

Any text in the data files can be a plain string, shown in every language, or
a mapping from language code to text:

    title:
      en: "Data Analyst"
      es: "Analista de Datos"

The language of a request is, in order: the `lang` cookie (set by the language
switcher), the browser's Accept-Language header, and DEFAULT_LANGUAGE. The
languages offered come from the LANGUAGES setting.
"""

import re
from typing import Any, Dict, List

from flask import current_app, g, has_app_context, has_request_context, request

LANG_COOKIE = "lang"

# Names used by the language switcher and in the chat's system prompt.
LANGUAGE_NAMES = {
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "it": "Italiano",
    "pt": "Português",
}

_LANGUAGE_CODE = re.compile(r"^[a-z]{2}$")

# English texts of the interface. text_config.yaml translates or overrides them
# under `ui` (e.g. ui.chat.thinking.es); a text it does not give for the
# visitor's language falls back to these.
UI_DEFAULTS: Dict[str, str] = {
    # Selector page and dock
    "selector.page_title": "Select Your Experience",
    "selector.subtitle": "How would you like to explore my portfolio?",
    "selector.cli_title": "Developer",
    "selector.cli_desc": "Interactive CLI experience.",
    "selector.recruiter_title": "Recruiter",
    "selector.recruiter_desc": "AI-powered chat assistant.",
    "selector.visual_title": "Visual",
    "selector.visual_desc": "Quick graphical overview.",
    "dock.home": "Go to Home Selector",
    "dock.cli": "Open Developer View",
    "dock.recruiter": "Open Recruiter View",
    "dock.visual": "Open Visual View",
    "dock.theme": "Switch Theme",
    "dock.info": "Show Info",
    "dock.language": "Change language",
    "view.render_error": "Error rendering view template.",
    # CLI window (browser side)
    "cli.input_label": "Command Input",
    "cli.auth_required": "Authentication required for CLI access.",
    "cli.welcome_fallback": "Welcome to the CLI portfolio!",
    "cli.hint_help": "Type 'help' for a list of available commands.",
    "cli.hint_theme": "Type 'theme light' or 'theme gruvbox' to change the look.",
    "cli.permission_denied": "Permission denied, please try again.",
    "cli.theme_current": "Current theme: '{theme}'.",
    "cli.theme_available": "Available themes: {themes}",
    "cli.theme_set": "Theme set to '{theme}'.",
    "cli.theme_not_found": "Error: Theme '{theme}' not found. Available: {themes}",
    "cli.no_token": "Authentication error: Session token not found. Please refresh.",
    "cli.session_expired": "Session expired. Please re-authenticate.",
    "cli.server_error": "Server error: {error}",
    # CLI command output (server side)
    "cli_out.name": "Name",
    "cli_out.title": "Title",
    "cli_out.summary": "Summary",
    "cli_out.no_summary": "No summary available.",
    "cli_out.skills_header": "[INFO] Technical Skills:",
    "cli_out.skills_unavailable": "  (Skills data unavailable)",
    "cli_out.experience_header": "[INFO] Experience:",
    "cli_out.experience_none": "  (No experience listed)",
    "cli_out.education_header": "[INFO] Education:",
    "cli_out.education_none": "  (No education listed)",
    "cli_out.contact_header": "[INFO] Contact Information:",
    "cli_out.contact_none": "  (No contact details available)",
    "cli_out.ls_usage": (
        "[ERROR] Unknown argument for 'ls'. Did you mean 'ls projects'?"
    ),
    "cli_out.ls_header": "[INFO] Projects (use 'show <id>' for details):",
    "cli_out.table_title": "Title",
    "cli_out.projects_unavailable": "  (Project data could not be loaded)",
    "cli_out.filter_usage": (
        "[ERROR] Usage: filter --tech <technology>. Example: filter --tech python"
    ),
    "cli_out.filter_none": "[INFO] No projects found with technology: '{tech}'",
    "cli_out.filter_header": "[INFO] Projects using '{tech}':",
    "cli_out.show_usage": "[ERROR] Usage: show <project_id>",
    "cli_out.show_not_found": ("[ERROR] Project '{id}' not found. Use 'ls projects'."),
    "cli_out.show_header": "--- Project: {title} ---",
    "cli_out.type": "[INFO] Type: {type}",
    # Labels of the project types; a type without one is shown capitalized.
    "project_type.webapp": "Web app",
    "project_type.mobile": "Mobile app",
    "project_type.library": "Library",
    "cli_out.description": "[INFO] Description:",
    "cli_out.no_description": "(No description)",
    "cli_out.technologies": "[INFO] Technologies:",
    "cli_out.not_specified": "  (Not specified)",
    "cli_out.links": "[LINK] Links:",
    "cli_out.link_live": "Live Demo",
    "cli_out.link_code": "Code Repo",
    "cli_out.link_pypi": "PyPI Page",
    "cli_out.link_docs": "Docs",
    "cli_out.no_links": "  (No external links available)",
    "cli_out.open_usage": "[ERROR] Usage: open <project_id>",
    "cli_out.open_not_found": "[ERROR] Project '{id}' not found.",
    "cli_out.open_no_url": "[INFO] Project '{id}' does not have a live URL to open.",
    "cli_out.opening": "Attempting to open {url} in a new tab...",
    "cli_out.links_header": "[INFO] Social & Repo Links:",
    "cli_out.links_none": "  (No social links configured)",
    "cli_out.neofetch_title": "Title",
    "cli_out.neofetch_projects": "Projects",
    "cli_out.neofetch_skills": "Skills",
    "cli_out.logo_not_found": "(Logo not found)",
    "cli_out.logo_unknown": "[ERROR] Logo '{logo}' not found. Available: {logos}",
    "cli_out.neofetch_usage": "[ERROR] Usage: neofetch [--logo [<name>]]",
    "cli_out.man_usage": "[ERROR] Usage: man <command>. Please specify a command.",
    "cli_out.man_none": "[ERROR] No manual entry for '{command}'.",
    "cli_out.command_not_found": "[ERROR] Command not found: '{command}'. Type 'help'.",
    "cli_out.internal_error": (
        "[ERROR] Internal server error occurred. Please check server logs."
    ),
    "cli_out.load_failed": "[ERROR] Failed to load backend data.",
    # Recruiter chat
    "chat.window_title": "Recruiter Assistant",
    "chat.loading": "Loading...",
    "chat.verifying": "Verifying code...",
    "chat.access_granted": "Access granted! Thank you. How can I help you?",
    "chat.ask_placeholder": "Ask about my skills or projects...",
    "chat.ask_another": "Ask another question...",
    "chat.wrong_code": "Sorry, that's not the correct code. Please try again.",
    "chat.code_placeholder": "Enter access code...",
    "chat.thinking": "Thinking...",
    "chat.session_expired": (
        "Your session has expired. Please enter the access code again."
    ),
    "chat.unavailable": "The AI assistant is currently unavailable.",
    "chat.error": "Sorry, an error occurred: {error}",
    "chat.welcome_back": "Welcome back! How can I assist you?",
    "chat.welcome_fallback": (
        "Hello! This chat requires an access code. Please enter it to continue."
    ),
    "chat.reply_not_configured": "Error: Chatbot not configured correctly.",
    "chat.reply_unavailable": (
        "Sorry, I'm having trouble connecting to the AI service. "
        "Please try again later."
    ),
    "chat.reply_too_many_rounds": (
        "Sorry, I couldn't put that answer together. Could you rephrase the question?"
    ),
    "chat.reply_empty": "Sorry, I don't have an answer for that.",
    "chat.language_hint": (
        "The visitor is browsing the site in {language}. Answer in the language "
        "of their question; if it is unclear, answer in {language}."
    ),
    # Visual view
    "visual.heading": "Project Showcase",
    "visual.loading": "Loading projects...",
    "visual.empty": "No projects to display.",
    "visual.load_error": "Could not load projects: {error}",
    "visual.overlay_live": "View Live Project",
    "visual.overlay_source": "View Source Code",
    "visual.overlay_go": "Go",
    "visual.link_live": "View Live",
    "visual.link_code": "Code",
    "visual.untitled": "Untitled Project",
    "visual.no_description": "No description available.",
    "visual.screenshot_alt": "{title} Screenshot",
}


def get_languages() -> List[str]:
    """Returns the languages the site offers, the first being the fallback."""
    if has_app_context():
        languages = current_app.config.get("LANGUAGES")
        if languages:
            return list(languages)
    return ["en"]


def get_default_language() -> str:
    """Returns DEFAULT_LANGUAGE if it is offered, else the first language."""
    languages = get_languages()
    default = current_app.config.get("DEFAULT_LANGUAGE") if has_app_context() else None
    return default if default in languages else languages[0]


def get_locale() -> str:
    """Returns the language of the current request."""
    if not has_request_context():
        return get_default_language()
    if "locale" not in g:
        languages = get_languages()
        chosen = request.cookies.get(LANG_COOKIE)
        if chosen not in languages:
            chosen = request.accept_languages.best_match(languages)
        g.locale = chosen or get_default_language()
    return str(g.locale)


def language_name(code: str) -> str:
    """Returns a language's own name, e.g. 'Español' for 'es'."""
    return LANGUAGE_NAMES.get(code, code.upper())


def is_localized(value: Any) -> bool:
    """Tells whether a value is a {language code: text} mapping.

    Its keys must all be two-letter codes, and at least one must be a language
    the site offers or knows by name, so that an ordinary mapping (e.g. social
    links) is never mistaken for one.
    """
    if not isinstance(value, dict) or not value:
        return False
    keys = list(value.keys())
    if not all(isinstance(k, str) and _LANGUAGE_CODE.match(k) for k in keys):
        return False
    known = set(get_languages()) | set(LANGUAGE_NAMES)
    return any(k in known for k in keys)


def localize(value: Any, lang: str | None = None) -> Any:
    """Resolves every localized mapping inside a value to one language.

    Falls back to the default language, then to the first translation given.
    Plain values are returned unchanged.
    """
    lang = lang or get_locale()
    if is_localized(value):
        for candidate in (lang, get_default_language()):
            if value.get(candidate) is not None:
                return localize(value[candidate], lang)
        return localize(next(iter(value.values())), lang)
    if isinstance(value, dict):
        return {k: localize(v, lang) for k, v in value.items()}
    if isinstance(value, list):
        return [localize(v, lang) for v in value]
    return value


def _ui_overrides(value: Any, lang: str, prefix: str = "") -> Dict[str, str]:
    """Turns the `ui` section into 'section.key' texts for one language.

    Unlike data texts, a translation missing for `lang` is skipped rather than
    replaced by another language, so the built-in English text is used.
    """
    if is_localized(value):
        text = value.get(lang)
        return {prefix.rstrip("."): str(text)} if text is not None else {}
    if isinstance(value, dict):
        flat: Dict[str, str] = {}
        for key, item in value.items():
            flat.update(_ui_overrides(item, lang, f"{prefix}{key}."))
        return flat
    if value is None or not prefix:
        return {}
    return {prefix.rstrip("."): str(value)}


def fill(template: str, **values: Any) -> str:
    """Fills {placeholders} without choking on other braces in the text."""
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template


def get_ui_texts() -> Dict[str, str]:
    """Returns the interface texts for the current language, as flat keys."""
    if not has_app_context():
        return dict(UI_DEFAULTS)
    if "ui_texts" not in g:
        # Imported here: utils needs this module to localize the data files.
        from app.common.utils import load_raw_text_config

        ui = load_raw_text_config().get("ui", {})
        if not isinstance(ui, dict):
            ui = {}
        texts = dict(UI_DEFAULTS)
        texts.update(_ui_overrides(ui, get_locale()))
        g.ui_texts = texts
    return dict(g.ui_texts)


def t(key: str, **values: Any) -> str:
    """Returns an interface text in the current language, placeholders filled."""
    return fill(get_ui_texts().get(key, key), **values)
