import logging

from flask import Flask

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_app(config_name="default"):
    """Flask application factory."""
    app = Flask(__name__.split(".")[0], instance_relative_config=False)

    try:
        app.config.from_object(f"config.Config")
    except ImportError:
        logging.error("Could not import config.Config.")
        app.config.from_mapping(SECRET_KEY="default-fallback-key-error")

    logging.info(f"App created with config: {config_name}")
    logging.info(f"App Root Path: {app.root_path}")

    with app.app_context():
        # Register Shell Blueprint
        from shell.routes import shell_bp

        app.register_blueprint(shell_bp)
        logging.info("Registered shell blueprint.")

        # Register CLI Blueprint
        from view_cli import cli_bp

        app.register_blueprint(cli_bp, url_prefix="/cli")
        logging.info("Registered cli blueprint with prefix /cli.")

        # Register Recruiter Blueprint
        from view_recruiter import recruiter_bp

        app.register_blueprint(recruiter_bp, url_prefix="/recruiter")
        logging.info("Registered recruiter blueprint with prefix /recruiter.")

        # --- Register Visual Blueprint ---
        from view_visual import visual_bp  # Import the blueprint

        app.register_blueprint(visual_bp, url_prefix="/visual")  # Register with prefix
        logging.info("Registered visual blueprint with prefix /visual.")

    @app.route("/health")
    def health_check():
        return "OK", 200

    return app
