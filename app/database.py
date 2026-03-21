from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _load_config() -> dict[str, Any]:
    config_path = Path(__file__).parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _build_database_url() -> str:
    config = _load_config()
    db_config = config.get("database", {})
    db_type = db_config.get("type", "mysql")

    if db_type == "sqlite":
        return "sqlite:///trade_system.db"

    mysql_config = db_config.get("mysql", {})
    user = mysql_config.get("user", "root")
    password = mysql_config.get("password", "")
    host = mysql_config.get("host", "localhost")
    port = mysql_config.get("port", "3306")
    database = mysql_config.get("database", "trade_system_db")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


DATABASE_URL = _build_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine_kwargs = {"future": True}
if IS_SQLITE:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
