from __future__ import annotations

from importlib import import_module
import os


create_app = import_module("backend.01_core.application").create_app
app = create_app()


def main() -> None:
    uvicorn = import_module("uvicorn")
    host = os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
