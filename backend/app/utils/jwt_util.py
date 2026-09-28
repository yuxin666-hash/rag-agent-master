"""
JWT Token 工具模块。
提供 token 生成、解析及路由保护装饰器。
"""
import datetime
import jwt
from functools import wraps
from flask import request, current_app

from app.utils.response import make_response


def generate_token(user_id: int, username: str) -> str:
    """
    生成 JWT Token，有效期读取自配置 JWT_EXPIRATION_DAYS。

    :param user_id: 用户 ID
    :param username: 用户名
    :return: 编码后的 JWT 字符串
    """
    expire_days = current_app.config.get('JWT_EXPIRATION_DAYS', 30)
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=expire_days),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def decode_token(token: str) -> dict | None:
    """
    解析并验证 JWT Token。

    :param token: JWT 字符串
    :return: payload 字典，验证失败返回 None
    """
    try:
        return jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_token_from_header() -> str | None:
    """
    从请求头中提取 Bearer Token。

    :return: token 字符串或 None
    """
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ', 1)[1]
    return None


def token_required(f):
    """
    路由装饰器：校验请求头中的 JWT Token。
    校验通过后在 flask.g 中注入 current_user_id 与 current_username。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return make_response(code=401, msg='缺少认证令牌')

        payload = decode_token(token)
        if not payload:
            return make_response(code=401, msg='令牌无效或已过期')

        from flask import g
        g.current_user_id = payload.get('user_id')
        g.current_username = payload.get('username')
        return f(*args, **kwargs)

    return decorated
