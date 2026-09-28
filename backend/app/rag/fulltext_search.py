"""
中文全文检索封装。
支持 zhparser（首选）与 pg_trgm（回退）两种模式，运行时自动检测。
"""
import os

# 修复 Windows 中文环境下 psycopg2 C 扩展的编码解析 bug
os.environ['PGCLIENTENCODING'] = 'utf8'

import psycopg2
from psycopg2.extras import RealDictCursor

from app.rag.config import RAGConfig


class FullTextSearch:
    """PostgreSQL 全文检索封装。"""

    def __init__(self):
        self.conn_params = {
            'host': RAGConfig.VECTOR_DB_HOST,
            'port': RAGConfig.VECTOR_DB_PORT,
            'dbname': RAGConfig.VECTOR_DB_NAME,
            'user': RAGConfig.VECTOR_DB_USER,
            'password': RAGConfig.VECTOR_DB_PASSWORD,
        }
        self._has_zhparser = self._check_zhparser()

    def _get_conn(self):
        params = dict(self.conn_params)
        params['client_encoding'] = 'utf8'
        return psycopg2.connect(**params)

    def _check_zhparser(self) -> bool:
        conn = None
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'zhparser'")
                return cur.fetchone() is not None
        except Exception:
            return False
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def search(self, query_text: str, topk: int = 20) -> list[dict]:
        """
        关键词检索。

        :param query_text: 查询文本
        :param topk: 返回数量
        :return: 结果列表，包含 id, source_path, category, dish_name, chunk_type, title, content, score
        """
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if self._has_zhparser:
                    cur.execute(
                        """
                        SELECT
                            id,
                            source_path,
                            category,
                            dish_name,
                            chunk_type,
                            title,
                            content,
                            ts_rank(to_tsvector('chinese', content), plainto_tsquery('chinese', %s)) AS score
                        FROM document_chunks
                        WHERE to_tsvector('chinese', content) @@ plainto_tsquery('chinese', %s)
                        ORDER BY score DESC
                        LIMIT %s
                        """,
                        (query_text, query_text, topk)
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            id,
                            source_path,
                            category,
                            dish_name,
                            chunk_type,
                            title,
                            content,
                            similarity(content, %s) AS score
                        FROM document_chunks
                        WHERE content %% %s
                        ORDER BY score DESC
                        LIMIT %s
                        """,
                        (query_text, query_text, topk)
                    )
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
