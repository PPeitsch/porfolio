# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Your new features here.

### Changed
- Your changed features here.

### Fixed
- Your fixed bugs here.


## [1.4.1] - 2025-06-19

### Fixed
- **Recruiter View Security**: Masked the access code input in the Recruiter chat view to prevent it from being displayed in plain text. This aligns its behavior with the CLI view for improved privacy. (Fixes #42)

### Refactored
- **CSS Utility**: Centralized the `.password-mask` style into the global stylesheet (`style.css`) to make it a reusable utility class and remove code duplication.


## [1.4.0] - 2025-06-19

### Added
- **Comprehensive Test Suite**: Implemented a full suite of unit and integration tests using `pytest`, achieving over 85% code coverage.
  - Added tests for `common` modules, including data loaders, caching logic, and the token decorator.
  - Implemented tests for the `auth` blueprint, covering success and failure cases for access code verification.
  - Added tests for all `view` API endpoints (`cli`, `recruiter`, `visual`), using mocks to isolate application logic from external services.
  - The test suite is now integrated into the CI pipeline, ensuring all future changes are validated.

### Changed
- **Test Infrastructure**: Refactored the test setup to use a central `conftest.py` for shared fixtures and a `helpers.py` module for utility functions, improving test maintainability and resolving import issues.


## [1.3.0] - 2025-06-18

### Changed
- **AI Chat Architecture**: The chat backend has been completely refactored from a static context-injection model to a dynamic "Function Calling" (or Tool Use) architecture.
  - The AI assistant now retrieves information on demand by calling specific Python functions (`get_project_details`, `get_skills`, etc.).
  - This new pattern ensures data is always up-to-date, reduces token usage, and provides a scalable foundation for more advanced tools.
- **LLM Service Layer**: The `LLMService` abstraction and its implementations have been updated to be "tool-aware," capable of sending tool definitions and parsing tool-use requests from the APIs.
- **Chat API**: The `/recruiter/api/chat` endpoint now orchestrates a multi-turn conversation loop, handling tool execution and providing results back to the LLM for final response synthesis.
- **Frontend Chat**: `chat.js` has been updated to manage and transmit conversation history, enabling contextual, multi-step dialogues.

### Removed
- **Static AI Context**: The `data/ai_context.md` file and its associated loader `load_ai_context()` have been removed, as they are now obsolete.


## [1.2.1] - 2025-06-17

### Changed
- Refactored `visual.css` to use global CSS variables, ensuring style consistency across views.

### Fixed
- **Code Clutter**: Removed the redundant `recruiter_story.yaml` data file and its corresponding unused loader function `load_recruiter_story_data` from `common/utils.py`.
- **Frontend**: Corrected a misleading comment in `terminal.js` regarding the session token key to accurately reflect that the authentication state is shared between views.


## [1.2.0] - 2025-06-17

### Added
- **Multi-Provider LLM Support**: The AI Chat Assistant now supports multiple LLM providers (Anthropic, OpenAI, and Google Gemini).
- **LLM Provider Configuration**: The active LLM provider can now be selected via an `LLM_PROVIDER` environment variable.
- **New Dependencies**: Added `openai` and `google-generativeai` libraries to support the new providers.

### Changed
- **LLM Service Abstraction**: Refactored the chat backend to use a Strategy design pattern.
  - A new `LLMService` abstract base class defines a common interface for all providers.
  - Provider-specific logic is now encapsulated in concrete service classes (`AnthropicService`, `OpenAIService`, `GeminiService`).
  - A factory function (`get_llm_service`) dynamically selects and instantiates the configured service, completely decoupling the chat endpoint from the specific LLM implementation.
- **Configuration**: Updated `config.py` and `.env.example` to include the new LLM provider settings and API keys.

### Fixed
- **Static Typing**: Resolved all `mypy` errors related to the new service classes and factory, ensuring the new architecture is type-safe.


## [1.1.0] - 2025-06-17

### Added
- **CLI Access Control**: Implemented a full authentication flow for the CLI view, mirroring the security of the Recruiter view.
  - The CLI now prompts for a password on initialization.
  - User authentication is handled via the existing `/auth/verify` endpoint.
  - All subsequent API requests from the CLI are now sent with a valid JWT.

### Changed
- **Shared Authentication State**: The JWT is now stored under a unified key (`app_access_token`) in `sessionStorage`, allowing the login session to be shared between the CLI and Recruiter views. Users no longer need to re-authenticate when switching between protected views.

### Fixed
- **CLI User Experience**:
  - Prevented the browser's native password manager from interfering with the terminal input by using a CSS-based masking technique instead of `type="password"`.
  - The password prompt now correctly hides user input for better privacy.


## [1.0.0] - 2025-06-15

### Added
- **AI-Powered Recruiter View**: Replaced the static "Choose Your Own Adventure" interface with a dynamic AI chat assistant, leveraging external LLM providers.
- **Secure Authentication System**:
  - Implemented a new `/auth` blueprint for JWT generation.
  - Gated the AI Chat view with a secret access code requested directly in the interface.
- **Enhanced CI/CD & Governance**:
  - Implemented structured YAML-based issue templates (`bug`, `feature`, `docs`).
  - Refactored CI into dedicated `code-quality` and `tests` workflows.
  - Added an automated `release` workflow triggered by git tags.
  - Formalized project guidelines (`CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`).
- **Unified UI Components**:
  - Created a reusable, draggable OS-style window component (`window.js`, `window.css`) for interactive views.
  - Added a modern navigation dock for seamless switching between views.
- **Project Setup**:
  - Added `.env.example` to document environment variables.
  - Established `requirements.in` files and a constraints-based workflow for dependency management via `pip-tools`.

### Changed
- **UI/UX Overhaul**: The CLI and Recruiter views now use the shared window component, unifying their look and feel. The old "Back" button is replaced by the new navigation dock.
- **Frontend Asset Loading**: Refactored `selector.js` to use `url_for`-generated paths, resolving all 404 errors for static assets.

### CI
- **Workflow Stability**: Resolved `bandit` and `pytest` errors by adding necessary configurations and placeholder tests, ensuring the CI pipeline passes successfully.
- **Dependency Conflicts**: Fixed version conflicts between production and development packages by pinning key dependencies and using a unified constraints file.
- **Codecov Integration**: Updated the Codecov action to the latest recommended configuration for robust coverage reporting.

### Fixed
- **Window Management**: Corrected bugs related to window minimizing, maximizing, and restoring for predictable behavior.
- **Static Asset Paths**: Resolved all 404 errors for CSS and JS files across all views.
- **Linting & Code Quality**: Addressed all `flake8` errors and standardized formatting.
- **Component Initialization**: Decoupled the window component from hard-coded dependencies, fixing initialization bugs.

### Security
- **API Protection**: The `/recruiter/api/chat` endpoint is now protected by a `@token_required` decorator, preventing unauthorized access and data scraping.
- **Safe String Comparison**: The authentication backend now uses `hmac.digest` to mitigate timing attacks.
