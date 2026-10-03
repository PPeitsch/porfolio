import os

from app.shell import create_app

# For now, default to development using the base Config
config_name = os.getenv("FLASK_CONFIG", "default")

app = create_app(config_name)

if __name__ == "__main__":
    # Development server only. The debugger runs code from the browser, so it
    # is off unless FLASK_DEBUG=1, and the server listens on localhost unless
    # FLASK_RUN_HOST says otherwise (e.g. 0.0.0.0 to reach it from the network).
    app.run(
        debug=os.getenv("FLASK_DEBUG") == "1",
        host=os.getenv("FLASK_RUN_HOST", "127.0.0.1"),
    )
