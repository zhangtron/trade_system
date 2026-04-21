from __future__ import annotations

import sitecustomize  # noqa: F401
import uvicorn


def _get_host_port():
    """从配置文件读取 host 和 port"""
    try:
        import yaml
        from pathlib import Path

        # 获取项目根目录（run.py 所在的目录）
        project_root = Path(__file__).parent
        config_path = project_root / "config.yaml"

        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                app_config = config.get("app", {})
                host = app_config.get("host", "0.0.0.0")
                port = app_config.get("port", 8899)
                print(f"📋 从配置文件读取: host={host}, port={port}")
                return host, port
        else:
            print(f"⚠️  配置文件不存在: {config_path}")
            print(f"📋 使用默认配置: host=0.0.0.0, port=8899")
    except Exception as e:
        print(f"⚠️  读取配置文件失败: {e}")
        print(f"📋 使用默认配置: host=0.0.0.0, port=8899")
    return "0.0.0.0", 8899


if __name__ == "__main__":
    host, port = _get_host_port()
    print(f"🚀 启动服务器: http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
