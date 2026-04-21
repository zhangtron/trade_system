"""
修改用户密码工具

支持修改任意用户的密码，包括管理员账户。
使用方法：
    python scripts/change_password.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from getpass import getpass
from sqlalchemy import select

from app.auth import get_password_hash
from app.database import SessionLocal, engine, Base
from app.models import User


def list_all_users():
    """列出所有用户"""
    db = SessionLocal()
    try:
        users = db.execute(select(User).order_by(User.user_id)).scalars().all()
        print("\n" + "="*60)
        print("系统用户列表：")
        print("="*60)
        for user in users:
            role_label = "管理员" if user.role == "admin" else "普通用户"
            status_label = "启用" if user.is_active else "禁用"
            print(f"ID: {user.user_id:3d} | 用户名: {user.username:15s} | "
                  f"角色: {role_label:6s} | 状态: {status_label}")
        print("="*60 + "\n")
        return users
    finally:
        db.close()


def change_password(username: str, new_password: str):
    """修改用户密码"""
    db = SessionLocal()
    try:
        user = db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()

        if not user:
            print(f"❌ 错误：用户 '{username}' 不存在")
            return False

        # 更新密码
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.refresh(user)

        print(f"✅ 成功：用户 '{username}' 的密码已更新")
        print(f"   用户ID: {user.user_id}")
        print(f"   用户名: {user.username}")
        print(f"   角色: {user.role}")
        print(f"   新密码: {new_password}")
        print()
        print("⚠️  重要提示：请妥善保管新密码！")
        return True

    except Exception as e:
        print(f"❌ 错误：修改密码失败 - {e}")
        db.rollback()
        return False
    finally:
        db.close()


def validate_password(password: str) -> bool:
    """验证密码强度"""
    if len(password) < 8:
        print("❌ 错误：密码长度至少为 8 位")
        return False

    # 检查密码强度（可选）
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not (has_upper and has_lower and has_digit):
        print("⚠️  警告：建议密码包含大小写字母和数字")

    return True


def main():
    """主函数"""
    import sys

    print("\n" + "="*60)
    print("密码修改工具")
    print("="*60 + "\n")

    # 显示所有用户
    users = list_all_users()

    # 获取用户名
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("请输入要修改密码的用户名: ").strip()

    if not username:
        print("❌ 错误：用户名不能为空")
        return

    # 获取新密码
    if len(sys.argv) > 2:
        new_password = sys.argv[2]
    else:
        new_password = getpass("请输入新密码: ")
        if not new_password:
            print("❌ 错误：密码不能为空")
            return

        # 确认密码
        confirm_password = getpass("请再次输入新密码: ")
        if new_password != confirm_password:
            print("❌ 错误：两次输入的密码不一致")
            return

    # 验证密码强度
    if not validate_password(new_password):
        return

    # 修改密码
    change_password(username, new_password)


if __name__ == "__main__":
    # 确保数据库表存在
    Base.metadata.create_all(bind=engine)
    main()
