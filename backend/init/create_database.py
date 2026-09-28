"""
独立脚本：创建 MySQL 数据库（若不存在）。

Usage:
    python init/create_database.py

配置来源：backend/.env 中的 DATABASE_URI
"""
import os
import sys
import pymysql
from urllib.parse import urlparse
from dotenv import load_dotenv

# 定位 backend 目录并加载 .env
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(backend_dir, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"错误：找不到 .env 文件，请从 .env.example 复制并配置。路径：{dotenv_path}")
    sys.exit(1)

DATABASE_URI = os.environ.get('DATABASE_URI')
if not DATABASE_URI:
    print("错误：环境变量 DATABASE_URI 未配置，请检查 .env 文件。")
    sys.exit(1)


def create_database():
    """根据 DATABASE_URI 解析连接信息并创建数据库（若不存在）。"""
    parsed = urlparse(DATABASE_URI)

    host = parsed.hostname
    port = parsed.port
    user = parsed.username
    password = parsed.password
    db_name = parsed.path.lstrip('/').split('?')[0]

    if not all([user, password, db_name]):
        print("错误：DATABASE_URI 格式不正确，无法解析用户名、密码或数据库名。")
        sys.exit(1)

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        charset='utf8mb4'
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        print(f'数据库 "{db_name}" 创建完成（或已存在）。')
    except pymysql.Error as e:
        print(f"数据库操作失败：{e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    create_database()
