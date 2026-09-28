"""
Flask 应用工厂模块。
"""
from flask import Flask
from flask_cors import CORS

from config import Config


def create_app(config_class=Config):
    """
    应用工厂函数，创建并配置 Flask 应用实例。

    :param config_class: 配置类
    :return: Flask 应用实例
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    from app.models import db
    db.init_app(app)
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
    )

    # 注册蓝图
    from app.routes.auth import bp as auth_bp
    from app.routes.chat import bp as chat_bp
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api')

    return app
