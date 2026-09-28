"""
认证服务层模块。
当前逻辑较简单，直接在路由层处理，保留此文件用于后续扩展。
"""


class AuthService:
    """
    用户认证相关服务。
    """

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        校验密码强度。

        :param password: 明文密码
        :return: (是否通过, 提示信息)
        """
        if len(password) < 6:
            return False, '密码长度不能少于6位'
        return True, ''
