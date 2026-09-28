"""
LangChain 工具定义。
为大模型提供检索菜谱文档的能力。
"""
from langchain_core.tools import tool

from app.rag.search_pipeline import SearchPipeline


@tool
def search_recipes(query: str) -> str:
    """
    搜索老乡鸡菜谱文档，获取菜品做法、配料、营养成分等信息。

    当用户询问以下问题时必须调用：
    - 某道菜的做法、步骤、怎么做
    - 某道菜的配料、食材、用了什么
    - 某道菜的营养成分、热量
    - 推荐菜品、有哪些菜、有什么类别
    - 菜品分类查询（如"有什么汤""推荐主食""有哪些炒菜"）

    :param query: 用户的查询问题，应包含菜品名、类别或关键词
    :return: 检索到的文档内容摘要
    """
    pipeline = SearchPipeline()
    result = pipeline.search(query)
    context = SearchPipeline.format_context(result['results'])
    return context
