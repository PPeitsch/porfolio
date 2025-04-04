from flask import Flask
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
basedir = os.path.abspath(os.path.dirname(__file__))


def create_app(config_name='default'):
    """Flask application factory."""
    # Use parent directory of shell as app root path for consistent template/static lookup
    app = Flask(__name__.split('.')[0],  # Use root package name
                instance_relative_config=False)

    app.config.from_object(f'config.Config')
    logging.info(f"App created with config: {config_name}")

    with app.app_context():
        # Register Shell Blueprint
        from shell import routes as shell_routes
        app.register_blueprint(shell_routes.shell_bp)
        logging.info("Registered shell blueprint.")

        # --- Register CLI Blueprint ---
        from view_cli import cli_bp  # Import the blueprint
        app.register_blueprint(cli_bp, url_prefix='/cli')  # Register with a prefix
        logging.info("Registered cli blueprint with prefix /cli.")

        # --- Register other view blueprints later ---
        # from view_recruiter import recruiter_bp
        # app.register_blueprint(recruiter_bp, url_prefix='/recruiter')
        # from view_visual import visual_bp
        # app.register_blueprint(visual_bp, url_prefix='/visual')

    @app.route('/health')
    def health_check():
        return "OK", 200

    return app
