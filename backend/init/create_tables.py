"""
独立脚本：创建所有数据表。

Usage:
    python init/create_tables.py

配置来源：backend/.env 中的 DATABASE_URI
"""
import os
import sys

# 将 backend 目录加入模块搜索路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv

dotenv_path = os.path.join(backend_dir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"错误：找不到 .env 文件，请从 .env.example 复制并配置。路径：{dotenv_path}")
    sys.exit(1)

from app import create_app
from app.models import db

app = create_app()


def create_tables():
    """在已存在的数据库中创建所有 SQLAlchemy 模型对应的表。"""
    with app.app_context():
        db.create_all()
        print('所有数据表创建完成。')


if __name__ == '__main__':
    create_tables()
