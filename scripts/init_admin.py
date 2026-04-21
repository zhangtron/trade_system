"""
Initialize admin user script.

This script creates a default admin user for the trading system.
Default credentials:
- Username: admin
- Password: admin123

IMPORTANT: Change the default password after first login in production!
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import UTC

from sqlalchemy import select

from app.auth import get_password_hash
from app.database import SessionLocal, engine
from app.models import Base, User, UserRole


def create_admin_user():
    """Create the default admin user if it doesn't exist."""
    db = SessionLocal()

    try:
        # Check if admin user already exists
        existing_admin = db.execute(
            select(User).where(User.username == "admin")
        ).scalar_one_or_none()

        if existing_admin:
            print("ℹ️  Admin user already exists")
            print(f"   Username: {existing_admin.username}")
            print(f"   Role: {existing_admin.role}")
            print(f"   Active: {existing_admin.is_active}")
            return

        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@localhost",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("✅ Admin user created successfully!")
        print(f"   User ID: {admin_user.user_id}")
        print(f"   Username: {admin_user.username}")
        print(f"   Password: admin123")
        print(f"   Role: {admin_user.role}")
        print()
        print("⚠️  IMPORTANT: Please change the default password after first login!")
        print("   You can change it using the user management API or directly in the database.")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Create all tables
    print("🔧 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified")
    print()

    # Create admin user
    print("🔧 Creating admin user...")
    create_admin_user()
