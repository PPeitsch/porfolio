# Contributing to the Unified Portfolio Project

First off, thank you for considering contributing! Your help is appreciated.

## How Can I Contribute?

There are many ways to contribute, including:

*   **Reporting Bugs:** If you find a bug, please create a bug report using the provided template. Include detailed steps to reproduce, expected behavior, and actual behavior. Check existing issues first.
*   **Suggesting Enhancements:** Open a feature request issue using the template. Explain the problem your feature solves and why it would be valuable.
*   **Writing Code:** Pick an open issue (especially those labeled `help wanted` or `good first issue`) and propose a solution via a Pull Request.
*   **Improving Documentation:** If you find gaps or errors in the README or other documentation, please submit a PR.
*   **Improving Styles/UI:** Suggestions or implementations for UI/UX improvements are welcome.

## Development Setup

1.  **Fork & Clone:** Fork the repository on GitHub and clone your fork locally.
    ```bash
    git clone https://github.com/PPeitsch/porfolio.git
    cd porfolio
    ```
2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate    # Windows
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    # Consider installing dev dependencies if a requirements-dev.txt exists
    # pip install -r requirements-dev.txt
    ```
4.  **Set up Environment:** Copy `.env.example` to `.env` if needed.
5.  **Run the App:**
    ```bash
    python run.py
    ```
6.  **Create a Branch:** Create a new branch for your feature or bug fix.
    ```bash
    git checkout -b feature/your-feature-name  # or fix/your-bug-fix
    ```

## Making Changes

*   **Code Style:** Please adhere to PEP 8 guidelines. Consider using formatters like Black and isort (configuration may be added later).
*   **Commit Messages:** Follow conventional commit message formats (like the one used in this project's steps, e.g., `feat(scope): description`).
*   **Testing:** If applicable, add tests for your changes. Ensure existing tests pass. (Test setup TBD).

## Submitting Pull Requests

1.  Push your changes to your fork:
    ```bash
    git push origin feature/your-feature-name
    ```
2.  Open a Pull Request (PR) against the `main` branch of the original repository.
3.  Fill out the PR template with details about your changes.
4.  Ensure any CI checks pass (Workflows TBD).
5.  Be prepared to discuss your changes and make adjustments based on feedback.

## Code of Conduct

By participating in this project, you are expected to uphold our **[Code of Conduct](CODE_OF_CONDUCT.md)**. <!-- Updated Link -->

Thank you for contributing!