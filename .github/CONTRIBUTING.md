# Contributing to the Unified Portfolio Project

First off, thank you for considering contributing! Your help is appreciated and this project is a welcoming place for contributors. Please read this document to understand how you can contribute.

## Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

- (a) The contribution was created in whole or in part by me and I have the right to submit it under the open source license indicated in the file; or
- (b) The contribution is based upon previous work that, to the best of my knowledge, is covered under an appropriate open source license and I have the right under that license to submit that work with modifications, whether created in whole or in part by me, under the same open source license (unless I am permitted to submit under a different license), as indicated in the file; or
- (c) The contribution was provided directly to me by some other person who certified (a), (b) or (c) and I have not modified it.
- (d) I understand and agree that this project and the contribution are public and that a record of the contribution (including all personal information I submit with it, including my sign-off) is maintained indefinitely and may be redistributed consistent with this project or the open source license(s) involved.

## How Can I Contribute?

### Reporting Bugs
If you find a bug, please check the [existing issues](https://github.com/PPeitsch/porfolio/issues) to see if it has already been reported. If not, please open a **Bug Report** using the provided template. Be sure to include:
- A clear and descriptive title.
- Detailed steps to reproduce the bug.
- What you expected to happen vs. what actually happened.
- Your environment details (OS, browser, etc.).

### Suggesting Enhancements
If you have an idea for a new feature or an improvement, please open a **Feature Request** using the provided template. Explain the problem your feature solves and why it would be a valuable addition to the project.

### Pull Requests
We welcome pull requests! To submit one:
1.  **Fork & Clone:** Fork the repository and clone it to your local machine.
2.  **Create a Branch:** Create a new branch for your changes with a descriptive name (e.g., `feat/add-new-cli-command` or `fix/visual-view-rendering-bug`).
3.  **Make Changes:** Write your code. Ensure it follows the project's coding style (enforced by `pre-commit` hooks).
4.  **Set Up Pre-Commit:** If you haven't already, install and set up the pre-commit hooks:
    ```bash
    pip install pre-commit
    pre-commit install
    ```
5.  **Commit Your Changes:** Use clear and descriptive commit messages. We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. A `commit-template.txt` is provided in the root to help.
    ```bash
    # Example commit message
    # feat(cli): Add 'neofetch' command for system summary
    #
    # Implements a new 'neofetch' command in the CLI view that displays a
    # visual summary of the portfolio, including name, title, and counts
    # for projects and skills, similar to the popular system information tool.
    ```
6.  **Push and Open PR:** Push your branch to your fork and open a pull request against the `main` branch of the original repository.
7.  **Fill out the Template:** The PR description will be pre-filled with a template. Please fill it out completely to help reviewers understand and test your changes.

## Development Setup
Follow the instructions in the `README.md` for a quick start on setting up your local development environment.

Thank you for contributing!
