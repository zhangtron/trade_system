from __future__ import annotations

import sitecustomize  # noqa: F401
import uvicorn


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8899, reload=False)
