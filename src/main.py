from src.backend.create_app import create_app
from src.backend.dependencies.settings import Settings
import uvicorn

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=Settings.flask_host,
        port=Settings.flask_port,
        reload=Settings.flask_debug,
    )
