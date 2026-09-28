"""
意图分析模块。
使用独立的非主对话 LLM 实例判断用户查询是否需要检索菜谱知识库。
避免将工具调用、检索过程污染主对话上下文。
"""
from langchain_core.messages import HumanMessage, SystemMessage

from app.rag.llm_helper import get_llm


_SYSTEM_PROMPT = (
    "你是查询意图分析专家。判断用户的问题是否需要查询菜谱数据库才能准确回答。"
    "需要查询的情况包括：询问菜品做法、配料、营养成分、推荐菜品、菜品分类、有什么菜等。"
    "不需要查询的情况包括：打招呼、闲聊、询问系统功能、与菜谱完全无关的问题。"
    "只回答'是'或'否'，不要解释。"
)


class IntentAnalyzer:
    """独立意图分析器，不污染主对话上下文。"""

    def __init__(self):
        self.llm = get_llm(temperature=0.1, max_tokens=64)

    def analyze(self, query: str, history_text: str = "") -> bool:
        """
        分析用户查询是否需要检索。

        :param query: 用户当前查询
        :param history_text: 历史对话文本摘要（可选，用于理解指代）
        :return: True 表示需要检索，False 表示不需要
        """
        prompt_parts = []
        if history_text:
            prompt_parts.append(f"历史对话：\n{history_text}")
        prompt_parts.append(f"用户当前问题：{query}")
        prompt_parts.append("这个问题是否需要查询菜谱数据库才能回答？只回答'是'或'否'。")

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content="\n".join(prompt_parts))
        ]
        response = self.llm.invoke(messages)
        content = str(response.content).strip().lower()
        return any(kw in content for kw in ["是", "yes", "需要", "true"])
