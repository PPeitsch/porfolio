import os

from shell import create_app

# For now, default to development using the base Config
config_name = os.getenv("FLASK_CONFIG", "default")

app = create_app(config_name)

if __name__ == "__main__":
    # Debug=True enables auto-reload and debugger
    # Host='0.0.0.0' makes it accessible on the network
    app.run(debug=True, host="0.0.0.0")  # nosec B104
