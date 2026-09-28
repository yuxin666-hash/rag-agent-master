"""
统一 API 响应格式封装。
"""


def make_response(code: int = 200, msg: str = 'success', data=None):
    """
    构造统一格式的 JSON 响应。

    :param code: 状态码，200 为成功
    :param msg: 提示消息
    :param data: 响应数据
    :return: Flask Response 对象
    """
    from flask import jsonify
    return jsonify({
        'code': code,
        'msg': msg,
        'data': data
    })
