"""
PostgreSQL + pgvector 初始化脚本。
创建数据库、扩展、表结构与索引。

Usage:
    python scripts/init_postgres.py

配置来源：backend/.env 中的 VECTOR_DB_* 变量
"""
import os
import sys

# 修复 Windows 中文环境下 psycopg2 C 扩展的编码解析 bug
os.environ['PGCLIENTENCODING'] = 'utf8'

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv(os.path.join(backend_dir, '.env'))

PG_HOST = os.environ.get('VECTOR_DB_HOST', 'localhost')
PG_PORT = int(os.environ.get('VECTOR_DB_PORT', '5432'))
PG_USER = os.environ.get('VECTOR_DB_USER', 'postgres')
PG_PASSWORD = os.environ.get('VECTOR_DB_PASSWORD', '')
PG_DATABASE = os.environ.get('VECTOR_DB_NAME', 'rag_vector')


def get_connection(dbname: str | None = None):
    """获取 PostgreSQL 连接。"""
    params = {
        'host': PG_HOST,
        'port': PG_PORT,
        'user': PG_USER,
        'password': PG_PASSWORD,
        'client_encoding': 'utf8',
    }
    if dbname:
        params['dbname'] = dbname
    return psycopg2.connect(**params)


def create_database():
    """创建数据库（若不存在）。"""
    conn = get_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT 1 FROM pg_database WHERE datname = %s',
                (PG_DATABASE,)
            )
            if not cur.fetchone():
                # 使用引号包裹防止数据库名包含特殊字符
                cur.execute(f'CREATE DATABASE "{PG_DATABASE}" ENCODING = \'UTF8\'')
                print(f'数据库 "{PG_DATABASE}" 创建成功。')
            else:
                print(f'数据库 "{PG_DATABASE}" 已存在。')
    finally:
        conn.close()


def init_extensions():
    """创建必要的扩展。"""
    conn = get_connection(PG_DATABASE)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            # pgvector
            cur.execute('CREATE EXTENSION IF NOT EXISTS vector;')
            print("扩展 'vector' 就绪。")

            # 中文分词：先尝试 zhparser
            try:
                cur.execute('CREATE EXTENSION IF NOT EXISTS zhparser;')
                cur.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_ts_config WHERE cfgname = 'chinese'
                        ) THEN
                            CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);
                            ALTER TEXT SEARCH CONFIGURATION chinese ADD MAPPING
                                FOR n,v,a,i,e,l,j,x WITH simple;
                        END IF;
                    END $$;
                """)
                print("扩展 'zhparser' 与 'chinese' 全文配置就绪。")
            except Exception as e:
                print(f"警告：zhparser 安装失败（{e}），回退到 pg_trgm。")
                cur.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
                print("扩展 'pg_trgm' 就绪（模糊匹配备用）。")
    finally:
        conn.close()


def create_tables():
    """创建文档块表与索引。"""
    conn = get_connection(PG_DATABASE)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    source_path TEXT NOT NULL,
                    category TEXT NOT NULL,
                    dish_name TEXT,
                    chunk_type TEXT NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    embedding VECTOR(1024),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            print("表 'document_chunks' 就绪。")

            # 检查 zhparser 是否可用
            cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'zhparser'")
            has_zhparser = cur.fetchone() is not None

            if has_zhparser:
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_fts
                    ON document_chunks USING GIN (to_tsvector('chinese', content));
                """)
                print("GIN 全文索引（chinese）已创建/已存在。")
            else:
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_trgm
                    ON document_chunks USING GIN (content gin_trgm_ops);
                """)
                print("GIN 模糊匹配索引（pg_trgm）已创建/已存在。")

            # HNSW 向量索引（高维向量高效近似搜索）
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding
                ON document_chunks USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            """)
            print("HNSW 向量索引已创建/已存在。")

            # 辅助索引
            cur.execute('CREATE INDEX IF NOT EXISTS idx_chunks_category ON document_chunks(category);')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_chunks_dish ON document_chunks(dish_name);')
            print("辅助索引已创建/已存在。")

        conn.commit()
    finally:
        conn.close()


if __name__ == '__main__':
    print(f'开始初始化 PostgreSQL 向量库：{PG_HOST}:{PG_PORT}/{PG_DATABASE}')
    create_database()
    init_extensions()
    create_tables()
    print('初始化完成。')
