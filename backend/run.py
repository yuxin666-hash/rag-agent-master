"""
应用启动入口。
"""
import os

# 修复 Windows 中文环境下 psycopg2 C 扩展的编码解析 bug
os.environ['PGCLIENTENCODING'] = 'utf8'

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
