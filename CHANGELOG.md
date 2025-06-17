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
  - Established `requirements.in` files for dependency management via `pip-tools`.

### Changed
- **UI/UX Overhaul**: The CLI and Recruiter views now use the shared window component, unifying their look and feel. The old "Back" button is replaced by the new navigation dock.
- **Frontend Asset Loading**: Refactored `selector.js` to use `url_for`-generated paths, resolving all 404 errors for static assets.

### Fixed
- **Window Management**: Corrected bugs related to window minimizing, maximizing, and restoring for predictable behavior.
- **Static Asset Paths**: Resolved all 404 errors for CSS and JS files across all views.
- **Linting & Code Quality**: Addressed all `flake8` errors and standardized formatting.
- **Component Initialization**: Decoupled the window component from hard-coded dependencies, fixing initialization bugs.

### Security
- **API Protection**: The `/recruiter/api/chat` endpoint is now protected by a `@token_required` decorator, preventing unauthorized access and data scraping.
- **Safe String Comparison**: The authentication backend now uses `hmac.compare_digest` to mitigate timing attacks.
