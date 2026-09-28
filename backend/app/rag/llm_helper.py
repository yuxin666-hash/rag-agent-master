"""
LLM 辅助模块。
提供统一的 LangChain LLM 初始化，避免各模块重复实现。
"""
import os

from langchain_core.language_models.chat_models import BaseChatModel


def get_llm(temperature: float = 0.3, max_tokens: int = 1024) -> BaseChatModel:
    """
    根据环境变量 LLM_PROVIDER 初始化对应的大模型。

    :param temperature: 采样温度
    :param max_tokens: 最大生成 token 数
    :return: LangChain ChatModel 实例
    :raises ValueError: 配置缺失或提供商不支持
    """
    provider = os.environ.get('LLM_PROVIDER', 'anthropic').lower()

    if provider == 'anthropic':
        from langchain_anthropic import ChatAnthropic
        kwargs: dict = {
            'model': os.environ.get('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            'anthropic_api_key': os.environ.get('ANTHROPIC_API_KEY'),
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        base_url = os.environ.get('ANTHROPIC_BASE_URL')
        if base_url:
            kwargs['anthropic_api_url'] = base_url
        return ChatAnthropic(**kwargs)

    elif provider == 'openai':
        from langchain_openai import ChatOpenAI
        kwargs: dict = {
            'model': os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            'api_key': os.environ.get('OPENAI_API_KEY'),
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        base_url = os.environ.get('OPENAI_BASE_URL')
        if base_url:
            kwargs['base_url'] = base_url
        return ChatOpenAI(**kwargs)

    else:
        raise ValueError(f'不支持的 LLM_PROVIDER: {provider}')
