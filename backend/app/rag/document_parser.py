"""
文档解析器。
递归读取 backend/data/ 下的分级目录与 markdown 文件。
"""
import os
import re
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class MarkdownDocument:
    """解析后的 Markdown 文档对象。"""
    source_path: str
    category: str           # 目录名，如"炒菜"
    file_name: str          # 文件名
    title: str              # 一级标题
    sections: list[dict] = field(default_factory=list)    # 二级标题内容块


def _find_readme(dir_path: str) -> str | None:
    """在目录中查找 README.md（大小写不敏感）。"""
    for name in os.listdir(dir_path):
        if name.lower() == 'readme.md':
            return os.path.join(dir_path, name)
    return None


def parse_markdown_file(file_path: str, category: str) -> MarkdownDocument:
    """
    解析单个 markdown 文件。

    结构要求：
    - 一级标题 # 菜品名称
    - 二级标题 ## 配料 / ## 步骤 / ## 营养成分 等
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取一级标题作为菜品名
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else os.path.splitext(os.path.basename(file_path))[0]

    # 按二级标题分块：匹配 ## 标题 及其后的内容（直到下一个 ## 或文件结束）
    sections = []
    pattern = r'^##\s+(.+?)\n(.*?)(?=^##\s+|\Z)'
    matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)

    for section_title, section_content in matches:
        sections.append({
            'title': section_title.strip(),
            'content': section_content.strip()
        })

    return MarkdownDocument(
        source_path=file_path,
        category=category,
        file_name=os.path.basename(file_path),
        title=title,
        sections=sections
    )


def parse_data_directory(data_dir: str | None = None) -> Iterator[MarkdownDocument]:
    """
    递归解析 data 目录下的所有 markdown 文件。

    :param data_dir: data 目录路径，默认 backend/data
    :yield: MarkdownDocument
    """
    if data_dir is None:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(backend_dir, 'data')

    if not os.path.exists(data_dir):
        raise FileNotFoundError(f'data 目录不存在：{data_dir}')

    for entry in os.scandir(data_dir):
        if not entry.is_dir() or entry.name.startswith('.') or entry.name.lower() == 'images':
            continue

        category = entry.name
        readme_path = _find_readme(entry.path)

        # 处理 README.md（品类概览）
        if readme_path:
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            yield MarkdownDocument(
                source_path=readme_path,
                category=category,
                file_name='README.md',
                title=f'{category}品类概览',
                sections=[{'title': '概览', 'content': readme_content}]
            )

        # 处理目录下的其他 .md 文件（具体菜品）
        for file_entry in os.scandir(entry.path):
            if (
                file_entry.is_file()
                and file_entry.name.lower().endswith('.md')
                and file_entry.name.lower() != 'readme.md'
            ):
                yield parse_markdown_file(file_entry.path, category)
