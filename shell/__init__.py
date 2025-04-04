from flask import Flask
import logging
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Define base directory if needed elsewhere
basedir = os.path.abspath(os.path.dirname(__file__))


def create_app(config_name='default'):
    """Flask application factory."""
    app = Flask(__name__,
                instance_relative_config=False,
                template_folder='templates',  # Explicitly set template folder
                static_folder='static'  # Explicitly set static folder
                )

    # Load configuration
    app.config.from_object(f'config.Config')  # Adjust path if config.py moves

    logging.info(f"App created with config: {config_name}")

    with app.app_context():
        # Register Blueprints for the shell
        from . import routes as shell_routes
        app.register_blueprint(shell_routes.shell_bp)
        logging.info("Registered shell blueprint.")

    @app.route('/health')
    def health_check():
        return "OK", 200

    return app
