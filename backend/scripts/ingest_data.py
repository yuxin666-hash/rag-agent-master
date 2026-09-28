"""
文档解析 → 分块 → 向量化 → 入库脚本。

Usage:
    python scripts/ingest_data.py

配置来源：backend/.env 中的 VECTOR_DB_* 与 EMBEDDING_* 变量
"""
import os
import sys

# 修复 Windows 中文环境下 psycopg2 C 扩展的编码解析 bug
os.environ['PGCLIENTENCODING'] = 'utf8'

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))

import psycopg2
from psycopg2.extras import execute_values

from app.rag.config import RAGConfig
from app.rag.document_parser import parse_data_directory
from app.rag.chunker import chunk_document
from app.rag.embedding import get_embedding_model


def get_connection():
    return psycopg2.connect(RAGConfig.get_vector_db_uri(), client_encoding='utf8')


def ingest():
    print("=" * 50)
    print("开始文档入库流程")
    print("=" * 50)

    # 1. 加载模型
    print("\n[1/4] 加载向量化模型...")
    embedder = get_embedding_model()
    print(f"      模型维度：{embedder.dimension}")

    # 2. 解析文档
    print("\n[2/4] 解析文档目录...")
    all_chunks = []
    doc_count = 0
    for doc in parse_data_directory():
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
        doc_count += 1

    print(f"      解析了 {doc_count} 个文档，生成 {len(all_chunks)} 个文本块")
    if not all_chunks:
        print("      没有可入库的文档，请检查 data/ 目录。")
        return

    # 3. 向量化
    print("\n[3/4] 计算向量...")
    texts = [chunk.content for chunk in all_chunks]
    embeddings = embedder.encode(texts, batch_size=16)

    # 4. 入库
    print("\n[4/4] 写入 PostgreSQL...")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE document_chunks;")

            values = []
            for chunk, emb in zip(all_chunks, embeddings):
                emb_str = '[' + ','.join(str(round(v, 6)) for v in emb) + ']'
                values.append((
                    chunk.source_path,
                    chunk.category,
                    chunk.dish_name,
                    chunk.chunk_type,
                    chunk.title,
                    chunk.content,
                    emb_str,
                    '{}'
                ))

            execute_values(
                cur,
                """
                INSERT INTO document_chunks
                (source_path, category, dish_name, chunk_type, title, content, embedding, metadata)
                VALUES %s
                """,
                values,
                template="(%s, %s, %s, %s, %s, %s, %s::vector, %s::jsonb)"
            )

        conn.commit()
        print(f"      成功入库 {len(values)} 条记录。")
    finally:
        conn.close()

    print("\n" + "=" * 50)
    print("文档入库完成")
    print("=" * 50)


if __name__ == '__main__':
    ingest()
