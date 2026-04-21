"""
生成并更新 SECRET_KEY

用于生产环境生成强随机密钥并更新到配置文件。
使用方法：
    python scripts/generate_secret_key.py
"""

import os
import secrets
from pathlib import Path


def generate_secret_key() -> str:
    """生成强随机密钥"""
    # 生成 64 字节的随机密钥（512 bits）
    return secrets.token_urlsafe(64)


def update_config_file(secret_key: str):
    """更新 config.yaml 文件"""
    # 获取项目根目录（scripts 的父目录）
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config.yaml"

    if not config_path.exists():
        print(f"❌ 错误：配置文件不存在 - {config_path}")
        return False

    try:
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 查找并更新 SECRET_KEY
        updated = False
        new_lines = []
        in_auth_section = False

        for line in lines:
            # 检查是否在 auth 部分
            if line.strip() == 'auth:':
                in_auth_section = True
                new_lines.append(line)
                continue

            # 检查 auth 部分结束
            if in_auth_section and line.startswith('  ') is False and line.strip():
                in_auth_section = False

            # 更新 secret_key
            if in_auth_section and 'secret_key:' in line:
                indent = len(line) - len(line.lstrip())
                new_lines.append(' ' * indent + f'secret_key: "{secret_key}"\n')
                updated = True
            else:
                new_lines.append(line)

        # 如果没有找到 auth 部分，添加它
        if not updated:
            # 查找 app 部分的位置
            insert_index = None
            for i, line in enumerate(new_lines):
                if line.strip() == 'app:':
                    # 在 app 部分之前插入 auth 部分
                    new_lines.insert(i, '\n')
                    new_lines.insert(i + 1, 'auth:\n')
                    new_lines.insert(i + 2, f'  # JWT 密钥，使用强随机密钥（自动生成于 {os.popen("date").read().strip()}）\n')
                    new_lines.insert(i + 3, f'  secret_key: "{secret_key}"\n')
                    new_lines.insert(i + 4, '  # Token 有效期（分钟）\n')
                    new_lines.insert(i + 5, '  access_token_expire_minutes: 1440\n')
                    new_lines.insert(i + 6, '  # 记住登录状态有效期（天）\n')
                    new_lines.insert(i + 7, '  remember_me_expire_days: 7\n')
                    break

        # 写回配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        print(f"✅ 成功：配置文件已更新 - {config_path}")
        return True

    except Exception as e:
        print(f"❌ 错误：更新配置文件失败 - {e}")
        return False


def verify_secret_key(secret_key: str) -> bool:
    """验证密钥强度"""
    # 检查长度
    if len(secret_key) < 32:
        print("⚠️  警告：密钥长度较短，建议至少 32 字符")
        return False

    # 检查是否包含足够的熵
    has_upper = any(c.isupper() for c in secret_key)
    has_lower = any(c.islower() for c in secret_key)
    has_digit = any(c.isdigit() for c in secret_key)
    has_special = any(c in '-_~.' for c in secret_key)

    if has_upper and has_lower and has_digit and has_special:
        print("✅ 密钥强度：良好")
        return True
    else:
        print("✅ 密钥强度：可接受")
        return True


def backup_config_file():
    """备份配置文件"""
    import shutil
    from datetime import datetime

    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        backup_path = config_path.parent / f"config.yaml.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(config_path, backup_path)
        print(f"✅ 备份已创建：{backup_path.name}")
        return True
    return False


def main():
    """主函数"""
    print("\n" + "="*70)
    print("SECRET_KEY 生成和更新工具")
    print("="*70 + "\n")

    # 生成新密钥
    print("🔐 正在生成强随机密钥...")
    secret_key = generate_secret_key()

    print(f"📋 生成的密钥（长度: {len(secret_key)} 字符）:")
    print("="*70)
    print(secret_key)
    print("="*70)
    print()

    # 验证密钥强度
    verify_secret_key(secret_key)
    print()

    # 确认更新
    response = input("是否要更新配置文件？(yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ 已取消操作")
        return

    # 备份配置文件
    print("\n📦 正在备份配置文件...")
    backup_config_file()

    # 更新配置文件
    print("\n📝 正在更新配置文件...")
    if update_config_file(secret_key):
        print()
        print("="*70)
        print("✅ 完成！")
        print("="*70)
        print()
        print("📌 后续步骤：")
        print("   1. 检查 config.yaml 确认密钥已更新")
        print("   2. 重启应用服务器")
        print("   3. 所有现有 Token 将失效，用户需要重新登录")
        print()
        print("⚠️  重要提示：")
        print("   - 请妥善保管此密钥，不要泄露给他人")
        print("   - 建议将 config.yaml 添加到 .gitignore 避免提交到版本控制")
        print("   - 定期更换密钥以提高安全性")
        print()
    else:
        print()
        print("❌ 更新失败，请手动修改 config.yaml")
        print(f"   在 auth 部分添加/修改：")
        print(f"   auth:")
        print(f"     secret_key: \"{secret_key}\"")
        print()


if __name__ == "__main__":
    main()
