import uvicorn

from backend.config import Settings
from backend.presentation.app_factory import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=Settings.flask_host,
        port=Settings.flask_port,
        reload=Settings.flask_debug,
    )
