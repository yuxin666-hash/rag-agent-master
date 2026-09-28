"""
查询重写模块。
使用独立 LLM 对话将用户口语化查询改写为标准检索语句。
不共享主对话上下文，避免检索需求污染聊天历史。
"""
from langchain_core.messages import HumanMessage, SystemMessage

from app.rag.llm_helper import get_llm


_SYSTEM_PROMPT = """你是一位专业的餐饮搜索查询优化专家。
用户的原始查询可能是口语化、不完整或带有歧义的。
你的任务是将用户查询改写为 1-3 条更适合文档检索的标准查询语句。

改写要求：
1. 保留用户的原始意图，不要添加不存在的信息
2. 将口语化表达改为正式菜名或烹饪术语（如"那个鸡汤"→"老母鸡汤的做法"）
3. 如果涉及配料、做法、营养等维度，请分别生成针对性查询
4. 如果查询涉及菜品类别路由（如"有哪些炒菜"），请保留类别关键词
5. 输出必须是纯文本，每行一条查询，不要编号、不要解释、不要多余说明"""


class QueryRewriter:
    """查询重写器。"""

    def __init__(self):
        self.llm = get_llm(temperature=0.2, max_tokens=256)

    def rewrite(self, query: str) -> list[str]:
        """
        重写用户查询为检索友好型查询列表。

        :param query: 用户原始查询
        :return: 改写后的查询列表（最多 3 条）
        """
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f'原始查询：{query}\n改写后的查询：')
        ]
        response = self.llm.invoke(messages)
        content = str(response.content)

        rewritten = [line.strip(' \t-•') for line in content.split('\n') if line.strip()]
        return rewritten[:3]
