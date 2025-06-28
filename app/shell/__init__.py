import logging

from flask import Flask

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_app(config_name="default"):
    """Flask application factory.

    This function is the entry point for creating the Flask application instance.
    It initializes the app, loads configuration, registers all necessary
    blueprints (shell, cli, recruiter, visual), and sets up a simple
    health check endpoint.

    Args:
        config_name (str): The name of the configuration to use.
                           Currently only 'default' is implemented.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__.split(".")[0], instance_relative_config=False)

    try:
        app.config.from_object("config.Config")
    except ImportError:
        logging.error(
            "Could not import config.Config. Ensure config.py is in the project root."
        )
        app.config.from_mapping(SECRET_KEY="default-fallback-key-error")  # nosec B106

    logging.info(f"App created with config: {config_name}")
    logging.info(f"App Root Path: {app.root_path}")

    with app.app_context():
        # Import and register all blueprints for the application
        from app.shell.routes import shell_bp

        app.register_blueprint(shell_bp)
        logging.info("Registered shell blueprint.")

        from app.auth import auth_bp

        app.register_blueprint(auth_bp, url_prefix="/auth")
        logging.info("Registered auth blueprint with prefix /auth.")

        from app.view_cli import cli_bp

        app.register_blueprint(cli_bp, url_prefix="/cli")
        logging.info("Registered cli blueprint with prefix /cli.")

        from app.view_recruiter import recruiter_bp

        app.register_blueprint(recruiter_bp, url_prefix="/recruiter")
        logging.info("Registered recruiter blueprint with prefix /recruiter.")

        from app.view_visual import visual_bp

        app.register_blueprint(visual_bp, url_prefix="/visual")
        logging.info("Registered visual blueprint with prefix /visual.")

    @app.route("/health")
    def health_check():
        """A simple health check endpoint."""
        return "OK", 200

    return app
