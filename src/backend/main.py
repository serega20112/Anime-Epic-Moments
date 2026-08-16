import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import uvicorn

from backend.config import Settings
from backend.presentation.app_factory import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=Settings.app_host,
        port=Settings.app_port,
        reload=Settings.app_debug,
    )
