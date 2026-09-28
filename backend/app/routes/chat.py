"""
聊天/问答相关路由模块。
支持 SSE 流式输出。

架构特点：
- 意图分析、检索结果整理均由独立 LLM 实例完成，不污染主对话消息历史。
- 主对话模型只负责最终回答生成，其消息列表中永远不会出现工具调用、检索原始文档等中间信息。
"""
import json
from flask import Blueprint, request, Response, stream_with_context

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.utils.response import make_response
from app.utils.jwt_util import token_required
from app.rag.llm_helper import get_llm
from app.rag.search_pipeline import SearchPipeline
from app.rag.intent_analyzer import IntentAnalyzer
from app.rag.context_rewriter import ContextRewriter
from app.services.llm_service import ChatService

bp = Blueprint('chat', __name__)


def _extract_text(content) -> str:
    """从 AIMessage/AIMessageChunk 的 content 中安全提取纯文本。
    兼容 Anthropic 等返回列表格式 content 的模型。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    texts.append(block.get('text', ''))
                elif block.get('type') == 'tool_use':
                    continue
            elif isinstance(block, str):
                texts.append(block)
        return ''.join(texts)
    return str(content) if content is not None else ''


def _sse(data: dict) -> str:
    """构造 SSE 数据行。"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@bp.route('/chat/sessions', methods=['POST'])
@token_required
def create_session():
    """创建新的对话 session。"""
    session_id = ChatService.create_session()
    return make_response(code=200, msg='创建成功', data={'session_id': session_id})


@bp.route('/chat/sessions', methods=['GET'])
@token_required
def list_sessions():
    """获取会话列表。"""
    sessions = ChatService.list_sessions()
    return make_response(code=200, msg='成功', data={'sessions': sessions})


@bp.route('/chat/sessions/<session_id>', methods=['GET'])
@token_required
def get_session(session_id):
    """获取指定会话的完整历史记录。"""
    if not ChatService.has_session(session_id):
        return make_response(code=404, msg='会话不存在')
    history = ChatService.get_history(session_id)
    return make_response(code=200, msg='成功', data={'session_id': session_id, 'messages': history})


@bp.route('/chat/sessions/<session_id>', methods=['DELETE'])
@token_required
def delete_session(session_id):
    """删除指定会话。"""
    success = ChatService.delete_session(session_id)
    if not success:
        return make_response(code=404, msg='会话不存在')
    return make_response(code=200, msg='删除成功')


@bp.route('/chat', methods=['POST'])
@token_required
def chat():
    """
    发送消息并获取大模型流式回复（SSE）。

    处理流程：
        1. 独立意图分析模型判断是否需要检索
        2. 如需检索：SearchPipeline 执行混合检索
        3. 独立知识整理模型重写/精炼检索结果
        4. 主对话模型基于精炼后的知识生成最终回答

    Request Body:
        - message: 用户消息（必填）
        - session_id: 现有会话 ID（可选，为空则新建）

    SSE Events:
        type=status  step=thinking|calling_tool|generating  message=...
        type=chunk   content=...
        type=done    session_id=...
    """
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    session_id = data.get('session_id')

    if not message:
        return make_response(code=400, msg='消息内容不能为空')

    # 确保 session 存在
    if not session_id or not ChatService.has_session(session_id):
        session_id = ChatService.create_session()

    # 保存用户消息
    ChatService.save_message(session_id, 'user', message)

    SYSTEM_PROMPT = (
        "你是老乡鸡菜谱智能问答助手，精通所有菜品。"
        "请基于提供的菜谱信息回答用户问题，语气友好、简洁。"
        "如果信息不足以回答，请诚实说明，不要编造内容。"
    )

    def generate():
        try:
            llm = get_llm(temperature=0.5, max_tokens=2048)

            # 获取历史并构建文本摘要（供独立模型使用）
            history = ChatService.get_history(session_id)
            history_text_lines = []
            for msg in history:
                label = '用户' if msg['role'] == 'user' else '助手'
                history_text_lines.append(f'{label}：{msg["content"]}')
            history_text = '\n'.join(history_text_lines)

            # ---------- Step 1: 独立意图分析 ----------
            yield _sse({
                'type': 'status',
                'step': 'thinking',
                'message': '正在分析查询意图...'
            })

            analyzer = IntentAnalyzer()
            needs_retrieval = analyzer.analyze(message, history_text)

            refined_context = ''
            rewritten_queries = []

            if needs_retrieval:
                # ---------- Step 2: 独立检索流程 ----------
                yield _sse({
                    'type': 'status',
                    'step': 'calling_tool',
                    'message': '正在检索菜谱信息...'
                })

                pipeline = SearchPipeline()
                search_result = pipeline.search(message)
                rewritten_queries = search_result['rewritten_queries']
                raw_context = SearchPipeline.format_context(search_result['results'])

                # ---------- Step 3: 独立知识整理 ----------
                rewriter = ContextRewriter()
                refined_context = rewriter.rewrite(message, raw_context, history_text)

            # ---------- Step 4: 主模型生成回答（消息历史完全干净）----------
            yield _sse({
                'type': 'status',
                'step': 'generating',
                'message': '正在生成回答...'
            })

            # 构建主对话消息列表，仅包含 System + 历史 User/Assistant 对话
            main_messages = [SystemMessage(content=SYSTEM_PROMPT)]
            for i, msg in enumerate(history):
                is_last = (i == len(history) - 1)
                if msg['role'] == 'user':
                    if is_last and refined_context:
                        # 最后一条用户消息注入精炼后的知识，替换原始问题
                        content = (
                            f'以下是与本次问题相关的整理后的菜谱信息：\n\n'
                            f'{refined_context}\n\n'
                            f'用户问题：{msg["content"]}\n\n'
                            f'请基于以上信息回答，语气友好、简洁。如果信息不足，请诚实说明，不要编造内容。'
                        )
                        main_messages.append(HumanMessage(content=content))
                    else:
                        main_messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    main_messages.append(AIMessage(content=msg['content']))

            full_reply = ''
            for chunk in llm.stream(main_messages):
                text = _extract_text(chunk.content)
                if text:
                    full_reply += text
                    yield _sse({'type': 'chunk', 'content': text})

            # 保存助手回复
            ChatService.save_message(session_id, 'assistant', full_reply)

            yield _sse({
                'type': 'done',
                'session_id': session_id,
                'rewritten_queries': rewritten_queries
            })

        except UnicodeDecodeError:
            yield _sse({'type': 'error', 'message': '数据库连接编码错误，请尝试以下方案：1) 删除 backend 下所有 __pycache__ 文件夹后重启；2) 或在 PowerShell 执行 $env:PYTHONUTF8=1; python run.py'})
        except ValueError as e:
            yield _sse({'type': 'error', 'message': str(e)})
        except Exception as e:
            yield _sse({'type': 'error', 'message': '服务繁忙，请稍后重试'})

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )
