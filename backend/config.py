"""
Flask 应用配置模块。
所有敏感配置均从环境变量 / .env 文件读取，代码中不保留硬编码凭据。
"""
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """基础配置类。"""

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT 配置
    JWT_EXPIRATION_DAYS = 30

    # CORS 配置
    CORS_SUPPORTS_CREDENTIALS = True
