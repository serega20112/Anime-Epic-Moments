from src.backend.create_app import create_app
from src.backend.dependencies.settings import Settings

app = create_app()

if __name__ == "__main__":
    app.run(
        host=Settings.flask_host,
        port=Settings.flask_port,
        debug=Settings.flask_debug
    )
