# Unified Portfolio Project 🎭

<!-- Badges -->
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.12+-blueviolet)](https://www.python.org)
[![Flask Version](https://img.shields.io/badge/Flask-3.0+-teal.svg)](https://flask.palletsprojects.com/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat)](https://pycqa.github.io/isort/)
[![Linting: Flake8](https://img.shields.io/badge/linting-flake8-yellowgreen)](https://flake8.pycqa.org/)
[![Code Quality](https://github.com/PPeitsch/porfolio/actions/workflows/code-quality.yml/badge.svg)](https://github.com/PPeitsch/porfolio/actions/workflows/code-quality.yml)
[![Tests](https://github.com/PPeitsch/porfolio/actions/workflows/tests.yml/badge.svg)](https://github.com/PPeitsch/porfolio/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/PPeitsch/porfolio/graph/badge.svg?token=PGot9fslGJ)](https://codecov.io/gh/PPeitsch/porfolio)
[![Contributions welcome](https://img.shields.io/badge/Contributions-welcome-brightgreen.svg?style=flat)](.github/CONTRIBUTING.md)

An interactive, multi-view portfolio website built with Python, Flask, and vanilla JavaScript. Features a terminal-style CLI, an AI-powered chat for recruiters, and a visual project showcase.

---

## 📸 Screenshots

<table>
  <tr>
    <td width="50%" align="center">
      <p><strong>1. View Selector</strong></p>
      <img src="docs/images/selector-view.png" alt="Screenshot of the initial view selector page" width="100%">
    </td>
    <td width="50%" align="center">
      <p><strong>2. Developer (CLI) View</strong></p>
      <img src="docs/images/cli-view.png" alt="Screenshot of the interactive terminal view" width="100%">
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <p><strong>3. Recruiter (AI Chat) View</strong></p>
      <img src="docs/images/recruiter-view.png" alt="Screenshot of the AI-powered chat assistant" width="100%">
    </td>
    <td width="50%" align="center">
      <p><strong>4. Visual Overview</strong></p>
      <img src="docs/images/visual-view.png" alt="Screenshot of the graphical project showcase" width="100%">
    </td>
  </tr>
</table>

## ✨ Features

*   **👤 Multi-Persona Interface:** Choose how you want to explore the portfolio:
    *   **💻 Developer View:** An interactive, draggable Command-Line Interface that simulates a desktop terminal experience.
    *   **🤖 Recruiter View:** An AI-powered chat assistant (powered by Anthropic, OpenAI, or Gemini) that answers natural language questions using dynamic function calling.
    *   **🖼️ Visual View:** A modern, graphical showcase of projects with hover effects and quick-access links.
*   **🔒 Secure & Modular Backend:**
    *   Built with an `app-layout` structure and Flask Blueprints for clean separation of concerns.
    *   Features a JWT-based authentication system to protect sensitive views (CLI & Recruiter) from unauthorized access.
*   **🔧 Highly Configurable:**
    *   Dynamic content (CV, projects, text templates) is loaded from simple `.yaml` and `.txt` files, making updates easy and code-free.
    *   LLM provider (Anthropic, OpenAI, Gemini) and specific models can be configured entirely through environment variables.
*   **✅ Quality Assured:** Enforces a high standard of code quality through a robust CI/CD pipeline and pre-commit hooks. Includes automated formatting (Black, isort), linting (Flake8), static type checking (MyPy), security scanning (Bandit), and a comprehensive test suite with over 80% coverage.

### 🔐 Authentication in Action
Both the CLI and Recruiter views are protected by a secure access code prompt to prevent unauthorized use.

<p align="center">
  <img src="docs/images/cli-auth-view.png" alt="Secure authentication prompt for the CLI" width="75%">
</p>

## 🚀 Quick Start & Development

1.  **Clone:** `git clone https://github.com/PPeitsch/porfolio.git`
2.  **Navigate:** `cd porfolio`
3.  **Create Environment:** `python -m venv venv && source venv/bin/activate`
4.  **Install Dependencies:** `pip install -r requirements-dev.txt`
5.  **Set Up Environment:**
    *   Copy `.env.example` to a new file named `.env`.
    *   Fill in the required values in `.env` (e.g., `SECRET_KEY`, `RECRUITER_ACCESS_CODE`, and the API key for your chosen `LLM_PROVIDER`).
6.  **Set Up Pre-Commit Hooks:** `pre-commit install`
7.  **Run:** `python run.py`
8.  Access at `http://127.0.0.1:5000`.

### 📦 Dependency Management

This project uses `pip-tools` for managing Python dependencies to ensure reproducible builds.

-   **Production** dependencies are listed in `requirements.in`.
-   **Development** dependencies are listed in `requirements-dev.in` (which now includes `pip-tools` itself).

After modifying an `.in` file, regenerate the locked `requirements` files by running the provided script:

```bash
# For Linux/macOS
./scripts/compile-reqs.sh

# For Windows (PowerShell)
./scripts/compile-reqs.ps1
```

## 🚢 Deployment

This Flask application is ready to be deployed using any production-ready WSGI server like Gunicorn or Waitress behind a reverse proxy like Nginx.

**Example using Gunicorn:**

```bash
# Ensure production environment variables are set
export FLASK_CONFIG=production
export FLASK_DEBUG=0
export SECRET_KEY='your-strong-production-secret-key'
export RECRUITER_ACCESS_CODE='your-production-access-code'
export LLM_PROVIDER='openai' # or 'anthropic', 'gemini'
export OPENAI_API_KEY='your-production-openai-key'

# Run with Gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8000 run:app
```

**Note:** The application uses a standard factory pattern (`create_app`), allowing for easy extension with different configurations (e.g., `production`, `testing`) if needed.

## 🤝 Contributing

Contributions are highly welcomed! Please see our **[Contributing Guidelines](.github/CONTRIBUTING.md)** before getting started.

## Code of Conduct

We are committed to providing a welcoming environment. Please review our **[Code of Conduct](.github/CODE_OF_CONDUCT.md)**.

## 🛡️ Security

Please refer to the **[Security Policy](.github/SECURITY.md)** for reporting vulnerabilities.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
An interactive experience, built with Python & ❤️ by <a href="https://github.com/PPeitsch" target="_blank">PPeitsch</a>.
</p>
