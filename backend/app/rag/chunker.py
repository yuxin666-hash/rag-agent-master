"""
文档分块器。
按目录结构 + 标题层级对文档进行合理分块，保证语义完整性与检索粒度。
"""
import re
from dataclasses import dataclass

from app.rag.document_parser import MarkdownDocument


@dataclass
class DocumentChunk:
    """分块后的文档单元。"""
    source_path: str
    category: str
    dish_name: str | None
    chunk_type: str       # category_overview / dish_title / dish_ingredients / dish_steps / dish_nutrition / dish_other
    title: str
    content: str


def _map_chunk_type(section_title: str) -> str:
    """根据二级标题映射 chunk_type。"""
    t = section_title.lower()
    if any(k in t for k in ('配料', '食材', '原料')):
        return 'dish_ingredients'
    if any(k in t for k in ('步骤', '做法', '制作', '流程', '烹饪')):
        return 'dish_steps'
    if any(k in t for k in ('营养', '成分', '热量', '健康')):
        return 'dish_nutrition'
    return 'dish_other'


def chunk_document(doc: MarkdownDocument) -> list[DocumentChunk]:
    """
    将单个 MarkdownDocument 拆分为多个 DocumentChunk。

    分块策略：
    1. 品类概览（README.md） -> category_overview（整篇为一个块）
    2. 菜品文档：
       a) dish_title 块：菜品名 + 一级标题下引言（所有二级标题前的前言）
       b) 各二级标题独立成块：ingredients / steps / nutrition / other
    """
    chunks: list[DocumentChunk] = []

    # ---------------- 品类概览 ----------------
    if doc.file_name.lower() == 'readme.md':
        chunks.append(DocumentChunk(
            source_path=doc.source_path,
            category=doc.category,
            dish_name=None,
            chunk_type='category_overview',
            title=doc.title,
            content=doc.sections[0]['content'] if doc.sections else ''
        ))
        return chunks

    # ---------------- 菜品文档 ----------------
    # 1. 标题块：菜品名 + 所有二级标题前的前言文字
    intro_parts = [f'菜品名称：{doc.title}']
    # 提取一级标题与第一个二级标题之间的正文（引言）
    with open(doc.source_path, 'r', encoding='utf-8') as f:
        raw = f.read()
    # 去掉一级标题行，取到第一个 ## 之前的内容
    body_after_title = re.sub(r'^#\s+.+?\n', '', raw, count=1, flags=re.MULTILINE)
    first_section_idx = body_after_title.find('\n## ')
    if first_section_idx != -1:
        intro_text = body_after_title[:first_section_idx].strip()
    else:
        intro_text = body_after_title.strip()
    if intro_text:
        intro_parts.append(f'简介：{intro_text[:600]}')

    chunks.append(DocumentChunk(
        source_path=doc.source_path,
        category=doc.category,
        dish_name=doc.title,
        chunk_type='dish_title',
        title=doc.title,
        content='\n'.join(intro_parts)
    ))

    # 2. 各二级标题独立成块
    for section in doc.sections:
        section_title = section['title']
        section_content = section['content']
        chunk_type = _map_chunk_type(section_title)

        full_content = f'{doc.title} - {section_title}\n{section_content}'

        # 控制块大小：如果内容过长，做简单截断（后续可引入语义滑窗）
        if len(full_content) > 1500:
            full_content = full_content[:1500] + '\n...（内容截断）'

        chunks.append(DocumentChunk(
            source_path=doc.source_path,
            category=doc.category,
            dish_name=doc.title,
            chunk_type=chunk_type,
            title=f'{doc.title} - {section_title}',
            content=full_content
        ))

    return chunks
