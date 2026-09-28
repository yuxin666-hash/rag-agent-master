"""
LLM 服务模块，基于 LangChain 实现多轮对话。
支持 Anthropic 与 OpenAI 根据环境变量动态切换。
"""
import os
import uuid
from typing import Optional, Iterator

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel

# 内存级 session 存储：{session_id: [messages]}
_chat_sessions: dict[str, list[dict]] = {}

_SYSTEM_PROMPT = (
    "你是一个专业的美食问答助手，精通老乡鸡菜谱。"
    "请用中文回答用户的问题，语气友好、专业。"
    "如果用户的问题与菜谱无关，请礼貌地引导用户询问菜谱相关问题。"
)


def _get_llm() -> BaseChatModel:
    """
    根据环境变量 LLM_PROVIDER 初始化对应的大模型。

    :return: LangChain ChatModel 实例
    :raises ValueError: 配置缺失或提供商不支持
    """
    provider = os.environ.get('LLM_PROVIDER', 'anthropic').lower()

    if provider == 'anthropic':
        from langchain_anthropic import ChatAnthropic
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError('Anthropic API Key 未配置')
        model = os.environ.get('ANTHROPIC_MODEL') or 'claude-3-haiku-20240307'
        base_url = os.environ.get('ANTHROPIC_BASE_URL') or None
        kwargs: dict = {'model': model, 'anthropic_api_key': api_key, 'max_tokens': 1024}
        if base_url:
            kwargs['anthropic_api_url'] = base_url
        return ChatAnthropic(**kwargs)

    elif provider == 'openai':
        from langchain_openai import ChatOpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OpenAI API Key 未配置')
        model = os.environ.get('OPENAI_MODEL') or 'gpt-3.5-turbo'
        base_url = os.environ.get('OPENAI_BASE_URL') or None
        kwargs: dict = {'model': model, 'openai_api_key': api_key}
        if base_url:
            kwargs['base_url'] = base_url
        return ChatOpenAI(**kwargs)

    else:
        raise ValueError(f'不支持的 LLM_PROVIDER: {provider}')


class ChatService:
    """聊天服务，管理对话 session 与 LangChain 调用。"""

    @staticmethod
    def create_session() -> str:
        """创建新的对话 session。"""
        session_id = str(uuid.uuid4())
        _chat_sessions[session_id] = []
        return session_id

    @staticmethod
    def get_history(session_id: str) -> list[dict]:
        """获取指定 session 的历史消息。"""
        return list(_chat_sessions.get(session_id, []))

    @staticmethod
    def list_sessions() -> list[dict]:
        """列出所有活跃 session。"""
        sessions = []
        for sid, messages in _chat_sessions.items():
            title = '新对话'
            if messages:
                first_user = next((m for m in messages if m['role'] == 'user'), None)
                if first_user:
                    title = first_user['content'][:20]
                    if len(first_user['content']) > 20:
                        title += '...'
            sessions.append({
                'session_id': sid,
                'title': title,
                'message_count': len(messages)
            })
        return sessions

    @staticmethod
    def has_session(session_id: str) -> bool:
        """判断 session 是否存在。"""
        return session_id in _chat_sessions

    @staticmethod
    def save_message(session_id: str, role: str, content: str) -> None:
        """保存一条消息到指定 session。"""
        if session_id in _chat_sessions:
            _chat_sessions[session_id].append({'role': role, 'content': content})

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """删除指定 session。"""
        if session_id in _chat_sessions:
            del _chat_sessions[session_id]
            return True
        return False

    @staticmethod
    def chat(session_id: Optional[str], message: str) -> dict:
        """
        发送消息并获取大模型完整回复（非流式）。

        :param session_id: 现有会话 ID，为空则自动创建
        :param message: 用户消息
        :return: {"reply": str, "session_id": str}
        :raises ValueError: 配置错误或调用失败
        """
        if not session_id or session_id not in _chat_sessions:
            session_id = ChatService.create_session()

        _chat_sessions[session_id].append({'role': 'user', 'content': message})

        history = _chat_sessions[session_id]
        lc_messages = [SystemMessage(content=_SYSTEM_PROMPT)]
        for msg in history:
            if msg['role'] == 'user':
                lc_messages.append(HumanMessage(content=msg['content']))
            else:
                lc_messages.append(AIMessage(content=msg['content']))

        llm = _get_llm()
        response = llm.invoke(lc_messages)
        reply = str(response.content)

        _chat_sessions[session_id].append({'role': 'assistant', 'content': reply})
        return {'reply': reply, 'session_id': session_id}

    @staticmethod
    def chat_stream(session_id: Optional[str], message: str) -> Iterator[dict]:
        """
        流式发送消息并逐块获取大模型回复。

        :param session_id: 现有会话 ID，为空则自动创建
        :param message: 用户消息
        :yield: {"chunk": str} 或 {"done": True, "session_id": str}
        :raises ValueError: 配置错误或调用失败
        """
        if not session_id or session_id not in _chat_sessions:
            session_id = ChatService.create_session()

        _chat_sessions[session_id].append({'role': 'user', 'content': message})

        history = _chat_sessions[session_id]
        lc_messages = [SystemMessage(content=_SYSTEM_PROMPT)]
        for msg in history:
            if msg['role'] == 'user':
                lc_messages.append(HumanMessage(content=msg['content']))
            else:
                lc_messages.append(AIMessage(content=msg['content']))

        llm = _get_llm()
        full_reply = ''

        for chunk in llm.stream(lc_messages):
            content = str(chunk.content)
            if content:
                full_reply += content
                yield {'chunk': content}

        _chat_sessions[session_id].append({'role': 'assistant', 'content': full_reply})
        yield {'done': True, 'session_id': session_id}
