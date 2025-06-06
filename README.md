# Unified Portfolio Project 🎭

<!-- Badges -->
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10+-blueviolet)](https://www.python.org)
[![Flask Version](https://img.shields.io/badge/Flask-2.3+-teal.svg)](https://flask.palletsprojects.com/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat)](https://pycqa.github.io/isort/)
[![Static Types: MyPy](https://img.shields.io/badge/static%20types-mypy-blue.svg)](https://mypy-lang.org/)
[![Linting: Flake8](https://img.shields.io/badge/linting-flake8-yellowgreen)](https://flake8.pycqa.org/)
[![CI Status](https://github.com/PPeitsch/porfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/PPeitsch/porfolio/actions/workflows/ci.yml)
[![Contributions welcome](https://img.shields.io/badge/Contributions-welcome-brightgreen.svg?style=flat)](.github/CONTRIBUTING.md)


A modern, multi-view portfolio website built with Flask, showcasing projects and skills tailored to different audiences (Developers, Recruiters, and General Visitors).

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
      <p><strong>3. Recruiter (CYOA) View</strong></p>
      <img src="docs/images/recruiter-view.png" alt="Screenshot of the guided 'Choose Your Own Adventure' view" width="100%">
    </td>
    <td width="50%" align="center">
      <p><strong>4. Visual Overview</strong></p>
      <img src="docs/images/visual-view.png" alt="Screenshot of the graphical project showcase" width="100%">
    </td>
  </tr>
</table>


## ✨ Features

*   **👤 Multi-Persona Interface:** Choose how you want to explore the portfolio:
    *   **💻 Developer Mode:** An interactive Command-Line Interface that fetches data from backend APIs.
    *   **🧭 Recruiter Path:** A guided "Choose Your Own Adventure" narrative that highlights relevant skills and project impact based on your choices.
    *   **🖼️ Visual Overview:** A modern, graphical showcase of projects with hover effects and quick-access links.
*   **🧩 Modular Structure:** Built with Flask Blueprints, simulating a micro-frontend architecture for clean separation of concerns.
*   **📝 Dynamic Content:** CV details, project information, and the recruiter story path are all loaded from simple `.yaml` files in the `/data` directory, making content updates easy and code-free.
*   **🚀 Modern Stack:** Python 3.10+, Flask, Tailwind CSS (via CDN), and vanilla JavaScript for dynamic view loading.
*   **✅ Quality Assured:** Enforces a high standard of code quality using `pre-commit` hooks for automated formatting (Black, isort), linting (Flake8), and static type checking (MyPy) on every commit.

## 📊 Project Status

*   **Phase 1 (Foundation & Shell):** ✅ Complete
*   **Phase 2 (CLI View):** ✅ Complete
*   **Phase 3 (Recruiter View):** ✅ Complete
*   **Phase 4 (Visual View):** ✅ Complete
*   **Phase 5 (Integration & Polish):** ✅ Complete
*   **Phase 6 (Documentation):** ✅ Complete
*   **Phase 7 (CI/CD & Deployment):** 🔄 In Progress

*(✅ Complete, 🔄 In Progress, ⏳ Not Started)*

## 🚀 Quick Start & Development

1.  **Clone:** `git clone https://github.com/PPeitsch/porfolio.git`
2.  **Navigate:** `cd porfolio`
3.  **Create Environment:** `python -m venv venv && source venv/bin/activate`
4.  **Install Dependencies:** `pip install -r requirements.txt -r requirements-dev.txt`
5.  **Set Up Pre-Commit Hooks:** `pre-commit install`
6.  **Run:** `python run.py`
7.  Access at `http://127.0.0.1:5000`.

For detailed contribution guidelines and manual quality checks, see [CONTRIBUTING.md](.github/CONTRIBUTING.md).

## 🚢 Deployment

This Flask application is ready to be deployed using any production-ready WSGI server like Gunicorn or Waitress behind a reverse proxy like Nginx.

**Example using Gunicorn:**

1.  **Install Gunicorn:**
    ```bash
    pip install gunicorn
    ```
2.  **Run the application:**
    *   The WSGI entry point is the `app` object created by the `create_app` factory. You can reference this using `run:app`.
    *   `--workers`: A good starting point is `(2 * number_of_cores) + 1`. For a 2-core machine, this is 5.
    *   `--bind`: The address and port to bind to. Use `0.0.0.0` to make it accessible externally.
    ```bash
    gunicorn --workers 4 --bind 0.0.0.0:8000 run:app
    ```
3.  **Environment Variables:**
    *   Ensure `FLASK_CONFIG` is set to `production` in your production environment (if you create a production config).
    *   Set a strong, unique `SECRET_KEY`.
    *   Set `FLASK_DEBUG=0`.

**Docker (Optional):**

A `Dockerfile` can be created to containerize the application for easier deployment on platforms like Docker Swarm, Kubernetes, or managed container services.

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
Built with Flask and a multi-persona approach.
</p>
