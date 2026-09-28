# 老乡鸡菜谱智能问答系统

基于 RAG（检索增强生成）的老乡鸡菜谱智能问答系统。核心设计理念：**主对话上下文永远不被检索过程污染** —— 意图分析、知识整理均由独立 LLM 实例完成，主模型只负责最终回答生成。

## 功能特性

- **智能问答**：支持菜品做法、配料、营养成分、菜品推荐等多维度问答
- **独立意图分析**：非主对话模型判断是否需要检索，主对话历史保持干净
- **混合检索**：语义检索（pgvector 余弦相似度）+ 中文全文检索（zhparser / pg_trgm），加权融合
- **独立知识整理**：检索结果经独立模型重写精炼后再注入主对话，避免原始文档污染上下文
- **查询重写**：自动将口语化查询改写为 1-3 条检索友好型查询
- **多轮对话**：基于 Session 的历史上下文记忆
- **SSE 流式输出**：实时展示思考 → 检索中 → 生成回答 的状态进度
- **历史对话管理**：侧边栏支持折叠/展开，可删除指定历史对话
- **自定义头像**：支持为对话双方配置头像图片，自动探测常见图片格式
- **用户系统**：JWT 认证，支持注册/登录/登出

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite |
| 后端 | Flask + Python 3.12+ |
| 向量数据库 | PostgreSQL 15 + pgvector |
| 业务数据库 | MySQL 8.0+ |
| LLM 框架 | LangChain（支持 Anthropic / OpenAI 切换） |
| Embedding | sentence-transformers（BAAI/bge-large-zh-v1.5） |

## 项目结构

```
rag-agent/
├── frontend/                  # React 前端
│   ├── src/
│   │   ├── components/        # Layout, Sidebar, MessageList, ChatBox, Avatar
│   │   ├── pages/             # ChatPage, LoginPage, RegisterPage
│   │   └── services/          # api.ts
│   ├── public/avatars/        # 对话头像图片（可选）
│   ├── .env.example
│   └── package.json
│
├── backend/                   # Flask 后端
│   ├── run.py                 # 启动入口 (port 5000)
│   ├── app/
│   │   ├── routes/            # auth.py, chat.py
│   │   ├── services/          # auth_service.py, llm_service.py
│   │   ├── models/            # user.py
│   │   ├── utils/             # jwt_util.py, response.py
│   │   └── rag/               # RAG 核心模块
│   │       ├── intent_analyzer.py    # 独立意图分析模型
│   │       ├── context_rewriter.py   # 独立知识整理模型
│   │       ├── search_pipeline.py    # 检索流程编排
│   │       ├── hybrid_search.py      # 混合检索（语义 + 全文）
│   │       ├── vector_store.py       # pgvector 语义检索
│   │       ├── fulltext_search.py    # PostgreSQL 中文全文检索
│   │       ├── query_rewriter.py     # 查询重写
│   │       ├── embedding.py          # 向量化模型封装（优先本地加载）
│   │       ├── document_parser.py    # Markdown 文档解析
│   │       └── chunker.py            # 文档分块
│   ├── data/                  # 菜谱 Markdown 源文件（按类别分目录）
│   ├── scripts/               # 数据库初始化与数据入库脚本
│   │   ├── init_postgres.py
│   │   └── ingest_data.py
│   ├── init/                  # MySQL 初始化脚本
│   │   ├── create_database.py
│   │   └── create_tables.py
│   ├── requirements.txt
│   └── .env.example
```

## 如何运行

### 1. 环境准备

确保本地已安装：
- Node.js 18+ 与 npm
- Python 3.12+
- MySQL 8.0+（已启动）
- PostgreSQL 15+（已启动）

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
```

编辑 `backend/.env`，至少配置以下项：

```env
# MySQL
DATABASE_URI=mysql+pymysql://root:123456@localhost:3306/rag_agent?charset=utf8mb4
SECRET_KEY=your-secret-key

# PostgreSQL / pgvector
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=5432
VECTOR_DB_NAME=rag_vector
VECTOR_DB_USER=postgres
VECTOR_DB_PASSWORD=123456

# LLM（二选一，通过 LLM_PROVIDER 切换）
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-xxx
ANTHROPIC_MODEL=claude-3-haiku-20240307

# Embedding
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_DEVICE=cpu
```

```bash
cd frontend
cp .env.example .env
```

编辑 `frontend/.env`：

```env
VITE_API_BASE_URL=/api
```

> **注意**：开发环境下**必须**使用 `/api`（由 Vite 代理转发到后端），不要写成 `http://localhost:5000/api`，否则会导致 CORS 凭证冲突。

### 3. 初始化数据库

**MySQL（用户数据）**：

```bash
cd backend
python init/create_database.py
python init/create_tables.py
```

**PostgreSQL + pgvector（向量库）**：

```bash
cd backend
python scripts/init_postgres.py
```

此脚本会：
- 创建 `rag_vector` 数据库
- 安装 `vector` 扩展（pgvector）
- 尝试安装 `zhparser`（中文分词），若失败则自动回退到 `pg_trgm`
- 创建 `document_chunks` 表及 HNSW 向量索引、GIN 全文索引

### 4. 菜谱数据入库

```bash
cd backend
python scripts/ingest_data.py
```

首次运行会自动从 Hugging Face 下载 `BAAI/bge-large-zh-v1.5` 向量模型（约 1.2GB），然后解析 `backend/data/` 下的 Markdown 文件、分块、计算向量并写入 PostgreSQL。

> **本地已有模型？** 如果 `backend/models/embeddings/` 下已存在模型文件，`embedding.py` 会自动优先使用本地路径加载，不会重复联网下载。

### 5. 启动服务

**后端**：

```bash
cd backend
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
python run.py
```

后端运行在 http://localhost:5000

**前端**：

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:5173

## 使用说明

1. 打开 http://localhost:5173，注册账号并登录
2. 进入「智能问答」页面
3. 输入问题，例如：
   - "宫保鸡丁怎么做"
   - "有什么主食推荐"
   - "老母鸡汤的营养成分"
4. 观察流式状态：
   - **正在分析查询意图...** → 独立模型判断是否需要检索
   - **正在检索菜谱信息...** → 执行混合检索（仅在需要时出现）
   - **正在生成回答...** → 主模型基于精炼知识流式输出最终答案

### 自定义头像（可选）

将图片放入 `frontend/public/avatars/` 目录：
- `user.xxx` — 用户头像
- `bot.xxx` — 助手头像

支持任意常见格式（`.png` / `.jpg` / `.jpeg` / `.webp` / `.gif`），组件会自动探测。如果未放置图片，则回退到默认渐变底色。

## 常见问题与解决方案

### 1. 前端请求报错 "网络请求失败" 或 CORS 错误

**原因**：前端 `.env` 里使用了 `http://localhost:5000/api` 且 `withCredentials=true`，与后端 CORS 配置冲突。

**解决**：将 `frontend/.env` 中的 `VITE_API_BASE_URL` 改为 `/api`，利用 Vite 代理转发。

### 2. Windows 下 psycopg2 报错 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xd6`

**原因**：Windows 中文环境下，psycopg2 C 扩展读取系统环境变量（如 PATH、USERPROFILE）时按 UTF-8 解码，但实际为 GBK 编码。

**解决**（三选一）：
- **方案 A**：删除 `backend` 下所有 `__pycache__` 文件夹后重启服务
- **方案 B**：在 PowerShell 中启动后端：`$env:PYTHONUTF8=1; python run.py`
- **方案 C**：确保系统环境变量中不包含中文路径，或设置 `PGCLIENTENCODING=utf8`

代码层面已在所有使用 psycopg2 的文件顶部设置 `os.environ['PGCLIENTENCODING'] = 'utf8'`，若仍报错优先尝试方案 A/B。

### 3. `init_postgres.py` 提示 `zhparser` 安装失败

**原因**：`zhparser` 是 PostgreSQL 第三方中文分词扩展，Windows 下通常需要手动编译安装，默认不存在。

**解决**：无需处理。脚本会自动回退到 `pg_trgm`（基于字符三元组的模糊匹配），检索功能仍可正常工作。如需更精准的中文分词检索，可额外安装 `zhparser` 后重新运行脚本。

### 4. `ingest_data.py` 首次运行长时间卡在 "加载向量化模型"

**原因**：首次使用 `sentence-transformers` 需要从 Hugging Face 下载 `BAAI/bge-large-zh-v1.5` 模型（约 1.2GB）。

**解决**：保持网络畅通等待下载完成。模型缓存到本地后，后续启动不再重复下载。缓存位置：
- Windows：`C:\Users\<用户名>\.cache\torch\sentence_transformers`
- Linux/macOS：`~/.cache/torch/sentence_transformers`

### 5. 本地已有模型，但运行时仍在尝试从 Hugging Face 下载

**原因**：`SentenceTransformer` 在传入模型名称时，即使本地有缓存也会先尝试连接 Hugging Face 做元数据校验。

**解决**：代码已自动探测 `backend/models/embeddings/` 下的本地快照路径，找到后直接使用本地路径加载。如仍出现，请删除 `backend/app/rag/__pycache__` 后重启后端。

### 6. 聊天时提示 "服务繁忙" 或 LLM 无响应

**排查步骤**：
1. 检查 `backend/.env` 中的 `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` 是否填写正确
2. 检查 `LLM_PROVIDER` 是否与配置的 Key 对应（`anthropic` 或 `openai`）
3. 查看后端控制台是否有具体报错堆栈
4. 确认 PostgreSQL 已启动且 `rag_vector` 数据库存在

### 7. 会话历史在重启后丢失

**原因**：当前 Session 存储为内存字典（`_chat_sessions`），未持久化到数据库。

**解决**：这是当前版本的已知设计。如需持久化，可将 Session 数据写入 MySQL 或 Redis。

### 8. 检索不到任何结果

**排查步骤**：
1. 确认已执行 `python scripts/ingest_data.py` 且输出显示成功入库了若干条记录
2. 使用 psql 检查表内数据：
   ```bash
   psql -h localhost -p 5432 -U postgres -d rag_vector
   SELECT COUNT(*) FROM document_chunks;
   ```
3. 确认 `backend/data/` 目录下存在 `.md` 文件
