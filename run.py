from __future__ import annotations

import sitecustomize  # noqa: F401
import uvicorn


def _get_host_port():
    try:
        import yaml
        from pathlib import Path
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                app_config = config.get("app", {})
                return app_config.get("host", "0.0.0.0"), app_config.get("port", 8899)
    except Exception:
        pass
    return "0.0.0.0", 8899


if __name__ == "__main__":
    host, port = _get_host_port()
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
