"""
检索流程编排。
整合查询重写、混合检索、结果格式化，对外提供统一入口。
"""
from app.rag.config import RAGConfig
from app.rag.query_rewriter import QueryRewriter
from app.rag.hybrid_search import HybridSearch


class SearchPipeline:
    """完整检索流程封装。"""

    def __init__(self):
        self.rewriter = QueryRewriter()
        self.searcher = HybridSearch()

    def search(self, query: str) -> dict:
        """
        执行完整检索流程。

        :param query: 用户原始查询
        :return: {"rewritten_queries": [...], "results": [...]}
        """
        rewritten = self.rewriter.rewrite(query)

        all_results = []
        seen_ids = set()

        for q in rewritten:
            results = self.searcher.search(q)
            for r in results:
                sid = str(r['id'])
                if sid not in seen_ids:
                    seen_ids.add(sid)
                    all_results.append(r)

        all_results.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)

        return {
            'rewritten_queries': rewritten,
            'results': all_results[:RAGConfig.RERANK_TOPK]
        }

    @staticmethod
    def format_context(results: list[dict]) -> str:
        """
        将检索结果格式化为 LLM 可用的上下文文本。

        :param results: 检索结果列表
        :return: 格式化字符串
        """
        if not results:
            return '未检索到相关文档。'

        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f'[{i}] {r.get("title", "未知")}')
            lines.append(f'    类别：{r.get("category", "-")}')
            if r.get('dish_name'):
                lines.append(f'    菜品：{r["dish_name"]}')
            lines.append(f'    内容：{r.get("content", "")}')
            lines.append('')
        return '\n'.join(lines)
