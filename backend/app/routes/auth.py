"""
用户认证相关路由模块。
"""
from flask import Blueprint, request, g

from app.models import db
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.response import make_response
from app.utils.jwt_util import generate_token, token_required, decode_token, get_token_from_header

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口。

    Request Body:
        - username: 用户名
        - password: 密码

    Returns:
        code: 200 成功，400 参数错误，409 用户已存在
    """
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return make_response(code=400, msg='用户名和密码不能为空')

    is_valid, msg = AuthService.validate_password_strength(password)
    if not is_valid:
        return make_response(code=400, msg=msg)

    existing = User.query.filter_by(username=username).first()
    if existing:
        return make_response(code=409, msg='该用户名已被注册')

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return make_response(code=200, msg='注册成功')


@bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口。

    Request Body:
        - username: 用户名
        - password: 密码

    Returns:
        code: 200 成功并返回 token，400 参数错误，401 认证失败
    """
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return make_response(code=400, msg='用户名和密码不能为空')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return make_response(code=401, msg='用户名或密码错误')

    token = generate_token(user.id, user.username)
    return make_response(
        code=200,
        msg='登录成功',
        data={'token': token, 'username': user.username}
    )


@bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """
    用户登出接口。
    JWT 无状态，后端无需额外处理，前端删除 token 即可。
    保留接口用于语义完整性及后续扩展黑名单机制。
    """
    return make_response(code=200, msg='登出成功')


@bp.route('/me', methods=['GET'])
def get_current_user():
    """
    获取当前登录用户信息。
    """
    token = get_token_from_header()
    if not token:
        return make_response(code=401, msg='未登录')

    payload = decode_token(token)
    if not payload:
        return make_response(code=401, msg='令牌无效或已过期')

    user = User.query.get(payload['user_id'])
    if not user:
        return make_response(code=401, msg='用户不存在')

    return make_response(code=200, msg='成功', data={'username': user.username})
