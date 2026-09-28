"""
用户模型模块。
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import db


class User(db.Model):
    """
    用户数据模型。

    Attributes:
        id: 主键
        username: 用户名，唯一
        password_hash: 加密后的密码哈希
        created_at: 注册时间
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str) -> None:
        """
        对用户密码进行哈希加密存储。

        :param password: 明文密码
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        校验密码是否正确。

        :param password: 明文密码
        :return: 是否匹配
        """
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """
        将用户对象序列化为字典（不含敏感信息）。

        :return: 用户数据字典
        """
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
