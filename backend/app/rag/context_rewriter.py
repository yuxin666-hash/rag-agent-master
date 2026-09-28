"""
检索结果重写模块。
使用独立的非主对话 LLM 实例整理检索到的原始文档，
使其更适合主对话模型使用，同时不污染主对话消息历史。
"""
from langchain_core.messages import HumanMessage, SystemMessage

from app.rag.llm_helper import get_llm


_SYSTEM_PROMPT = (
    "你是知识整理专家。请根据用户问题和检索到的原始菜谱信息，整理出一段简洁、准确、"
    "有针对性的回答素材。保留关键事实（菜名、配料、步骤、营养成分），删除与用户问题无关的信息。"
    "如果信息不足以回答问题，明确标注'信息不足'。用中文输出。"
)


class ContextRewriter:
    """独立上下文重写器，不污染主对话上下文。"""

    def __init__(self):
        self.llm = get_llm(temperature=0.3, max_tokens=1024)

    def rewrite(self, query: str, raw_context: str, history_text: str = "") -> str:
        """
        整理检索结果。

        :param query: 用户当前查询
        :param raw_context: 检索到的原始文档（SearchPipeline.format_context 输出）
        :param history_text: 历史对话文本摘要（可选）
        :return: 整理后的知识素材
        """
        prompt_lines = []
        if history_text:
            prompt_lines.append(f"历史对话：\n{history_text}")
        prompt_lines.append(f"用户当前问题：{query}")
        prompt_lines.extend([
            "",
            "检索到的原始信息：",
            raw_context,
            "",
            "请整理出一段简洁、准确、有针对性的回答素材，保留关键事实，删除无关信息。"
        ])

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content="\n".join(prompt_lines))
        ]
        response = self.llm.invoke(messages)
        return str(response.content)
