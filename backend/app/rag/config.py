"""
RAG 模块配置。
所有配置均从环境变量 / .env 文件读取。
"""
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
load_dotenv(os.path.join(basedir, '.env'))


class RAGConfig:
    """RAG 专用配置类。"""

    # PostgreSQL 向量库
    VECTOR_DB_HOST = os.environ.get('VECTOR_DB_HOST', 'localhost')
    VECTOR_DB_PORT = int(os.environ.get('VECTOR_DB_PORT', '5432'))
    VECTOR_DB_NAME = os.environ.get('VECTOR_DB_NAME', 'rag_vector')
    VECTOR_DB_USER = os.environ.get('VECTOR_DB_USER', 'postgres')
    VECTOR_DB_PASSWORD = os.environ.get('VECTOR_DB_PASSWORD', '')

    @classmethod
    def get_vector_db_uri(cls) -> str:
        """获取 PostgreSQL 连接 URI。"""
        return (
            f"postgresql://{cls.VECTOR_DB_USER}:{cls.VECTOR_DB_PASSWORD}"
            f"@{cls.VECTOR_DB_HOST}:{cls.VECTOR_DB_PORT}/{cls.VECTOR_DB_NAME}"
        )

    # 模型配置
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'BAAI/bge-large-zh-v1.5')
    EMBEDDING_DEVICE = os.environ.get('EMBEDDING_DEVICE', 'cpu')
    RERANKER_MODEL = os.environ.get('RERANKER_MODEL', 'BAAI/bge-reranker-large')
    MODEL_CACHE_DIR = os.path.join(basedir, 'models')

    # 检索配置
    VECTOR_TOPK = int(os.environ.get('VECTOR_TOPK', '20'))
    KEYWORD_TOPK = int(os.environ.get('KEYWORD_TOPK', '20'))
    RERANK_TOPK = int(os.environ.get('RERANK_TOPK', '5'))

    # 中文全文检索配置（运行时自动检测）
    FULLTEXT_CONFIG = 'chinese'
