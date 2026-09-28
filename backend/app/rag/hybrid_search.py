"""
混合检索 + Rerank 融合。
结合语义相似度与关键词匹配，加权融合后精排返回 Top-K。
"""
from app.rag.config import RAGConfig
from app.rag.vector_store import VectorStore
from app.rag.fulltext_search import FullTextSearch


class HybridSearch:
    """
    混合检索器。

    检索流程：
    1. 并行执行语义检索（pgvector 余弦相似度）与关键词检索（全文索引）
    2. 分别归一化后按权重加权融合
    3. 对融合结果按 hybrid_score 排序
    4. 标题类块（dish_title / category_overview）轻微加权提升
    5. 返回 Top-K
    """

    def __init__(self):
        self.vector_store = VectorStore()
        self.fulltext_search = FullTextSearch()
        self.vector_weight = 0.6
        self.keyword_weight = 0.4

    def search(self, query_text: str, topk: int = None) -> list[dict]:
        """
        执行混合检索并返回精排后的 Top-K 结果。

        :param query_text: 查询文本
        :param topk: 最终返回数量，默认读取 RAGConfig.RERANK_TOPK
        :return: 精排后的结果列表，每条包含 hybrid_score
        """
        if topk is None:
            topk = RAGConfig.RERANK_TOPK

        # 1. 并行执行两种检索
        semantic_results = self.vector_store.search(query_text, topk=RAGConfig.VECTOR_TOPK)
        keyword_results = self.fulltext_search.search(query_text, topk=RAGConfig.KEYWORD_TOPK)

        # 2. 加权融合（归一化后相加）
        merged: dict[str, dict] = {}

        if semantic_results:
            max_sem = max(r['score'] for r in semantic_results)
            for r in semantic_results:
                sid = str(r['id'])
                norm = (r['score'] / max_sem * self.vector_weight) if max_sem > 0 else 0
                merged[sid] = {**r, 'hybrid_score': norm}

        if keyword_results:
            max_kw = max(r['score'] for r in keyword_results)
            for r in keyword_results:
                sid = str(r['id'])
                norm = (r['score'] / max_kw * self.keyword_weight) if max_kw > 0 else 0
                if sid in merged:
                    merged[sid]['hybrid_score'] += norm
                else:
                    merged[sid] = {**r, 'hybrid_score': norm}

        # 3. 排序
        candidates = list(merged.values())

        # 4. 简单 Rerank：标题类块加权
        for c in candidates:
            if c.get('chunk_type') in ('dish_title', 'category_overview'):
                c['hybrid_score'] *= 1.1

        candidates.sort(key=lambda x: x['hybrid_score'], reverse=True)
        return candidates[:topk]
