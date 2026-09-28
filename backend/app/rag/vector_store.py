"""
向量存储封装。
基于 pgvector 提供语义检索能力。
"""
import os

# 修复 Windows 中文环境下 psycopg2 C 扩展的编码解析 bug
os.environ['PGCLIENTENCODING'] = 'utf8'

import psycopg2
from psycopg2.extras import RealDictCursor

from app.rag.config import RAGConfig
from app.rag.embedding import get_embedding_model


class VectorStore:
    """pgvector 向量检索封装。"""

    def __init__(self):
        self.conn_params = {
            'host': RAGConfig.VECTOR_DB_HOST,
            'port': RAGConfig.VECTOR_DB_PORT,
            'dbname': RAGConfig.VECTOR_DB_NAME,
            'user': RAGConfig.VECTOR_DB_USER,
            'password': RAGConfig.VECTOR_DB_PASSWORD,
        }

    def _get_conn(self):
        params = dict(self.conn_params)
        params['client_encoding'] = 'utf8'
        return psycopg2.connect(**params)

    @staticmethod
    def _vec_to_str(vec: list[float]) -> str:
        return '[' + ','.join(str(round(v, 6)) for v in vec) + ']'

    def search(self, query_text: str, topk: int = 20) -> list[dict]:
        """
        语义检索：根据查询文本返回最相似的文档块（余弦相似度）。

        :param query_text: 查询文本
        :param topk: 返回数量
        :return: 结果列表，包含 id, source_path, category, dish_name, chunk_type, title, content, score
        """
        embedder = get_embedding_model()
        query_vec = embedder.encode(query_text)[0]
        vec_str = self._vec_to_str(query_vec)

        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
                        1 - (embedding <=> %s::vector) AS score
                    FROM document_chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (vec_str, vec_str, topk)
                )
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
