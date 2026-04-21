from __future__ import annotations

from datetime import datetime, timedelta, UTC
from enum import Enum
from pathlib import Path
from typing import Annotated

import yaml
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole


def _get_config():
    """Load configuration from config.yaml"""
    try:
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception:
        pass
    return {}


config = _get_config()

# Security configuration
SECRET_KEY = config.get("auth", {}).get(
    "secret_key",
    "your-secret-key-change-this-in-production-min-32-chars"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
REMEMBER_ME_EXPIRE_DAYS = 7

# Password hashing
# Use bcrypt with deprecated='auto' for better compatibility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: bool = False


class UserCreate(BaseModel):
    username: str
    email: str | None = None
    password: str
    full_name: str | None = None
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    user_id: int
    username: str
    email: str | None
    full_name: str | None
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    # Ensure password doesn't exceed bcrypt's 72 byte limit
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise ValueError("Password too long (max 72 bytes)")
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Authenticate a user by username and password."""
    user = db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    # Update last login time
    user.last_login = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db),
) -> User:
    """Get the current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # Convert user_id to integer (JWT claims are strings by default)
        user_id = int(user_id)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


async def get_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """Get the current admin user (raises if not admin)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

