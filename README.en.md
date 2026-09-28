# Lao Xiang Ji (老乡鸡) Recipe Intelligent Q&A System

A RAG (Retrieval-Augmented Generation) based intelligent Q&A system for Lao Xiang Ji (a Chinese fast-food chain) recipes.

**Core design principle**: The main conversation context is **never polluted by the retrieval process**. Intent analysis and knowledge refinement are both handled by independent LLM instances; the main model only generates the final answer.

## Features

- **Intelligent Q&A**: Supports questions about cooking steps, ingredients, nutrition facts, and dish recommendations
- **Independent Intent Analysis**: A non-main-dialogue model decides whether retrieval is needed, keeping the main chat history clean
- **Hybrid Retrieval**: Semantic search (pgvector cosine similarity) + Chinese full-text search (zhparser / pg_trgm) with weighted fusion
- **Independent Context Rewriting**: Retrieved results are refined by an independent model before being injected into the main dialogue, preventing raw document pollution
- **Query Rewriting**: Automatically rewrites colloquial queries into 1-3 retrieval-friendly queries
- **Multi-turn Conversation**: Session-based historical context memory
- **SSE Streaming**: Real-time status feedback — analyzing intent → retrieving → generating
- **Conversation History Management**: Collapsible sidebar with the ability to delete specific conversations
- **Custom Avatars**: Supports configuring avatar images for both sides of the conversation, with automatic detection of common image formats
- **User System**: JWT authentication with registration, login, and logout

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Vite |
| Backend | Flask + Python 3.12+ |
| Vector DB | PostgreSQL 15 + pgvector |
| Business DB | MySQL 8.0+ |
| LLM Framework | LangChain (Anthropic / OpenAI switchable) |
| Embedding | sentence-transformers (BAAI/bge-large-zh-v1.5) |

## Project Structure

```
rag-agent/
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # Layout, Sidebar, MessageList, ChatBox, Avatar
│   │   ├── pages/             # ChatPage, LoginPage, RegisterPage
│   │   └── services/          # api.ts
│   ├── public/avatars/        # Avatar images (optional)
│   ├── .env.example
│   └── package.json
│
├── backend/                   # Flask backend
│   ├── run.py                 # Entry point (port 5000)
│   ├── app/
│   │   ├── routes/            # auth.py, chat.py
│   │   ├── services/          # auth_service.py, llm_service.py
│   │   ├── models/            # user.py
│   │   ├── utils/             # jwt_util.py, response.py
│   │   └── rag/               # RAG core modules
│   │       ├── intent_analyzer.py    # Independent intent analysis model
│   │       ├── context_rewriter.py   # Independent knowledge refinement model
│   │       ├── search_pipeline.py    # Retrieval pipeline orchestration
│   │       ├── hybrid_search.py      # Hybrid retrieval (semantic + full-text)
│   │       ├── vector_store.py       # pgvector semantic search
│   │       ├── fulltext_search.py    # PostgreSQL Chinese full-text search
│   │       ├── query_rewriter.py     # Query rewriting
│   │       ├── embedding.py          # Embedding model wrapper (local-first loading)
│   │       ├── document_parser.py    # Markdown document parser
│   │       └── chunker.py            # Document chunking
│   ├── data/                  # Recipe Markdown source files (by category)
│   ├── scripts/               # DB initialization and data ingestion
│   │   ├── init_postgres.py
│   │   └── ingest_data.py
│   ├── init/                  # MySQL initialization
│   │   ├── create_database.py
│   │   └── create_tables.py
│   ├── requirements.txt
│   └── .env.example
```

## How to Run

### 1. Prerequisites

Ensure the following are installed and running:
- Node.js 18+ and npm
- Python 3.12+
- MySQL 8.0+
- PostgreSQL 15+

### 2. Environment Variables

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`. At minimum, configure:

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

# LLM (choose one, switched via LLM_PROVIDER)
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

Edit `frontend/.env`:

```env
VITE_API_BASE_URL=/api
```

> **Note**: In development, you **must** use `/api` (forwarded by the Vite proxy). Do **not** use `http://localhost:5000/api`, as this causes a CORS credentials conflict.

### 3. Initialize Databases

**MySQL (user data)**:

```bash
cd backend
python init/create_database.py
python init/create_tables.py
```

**PostgreSQL + pgvector (vector store)**:

```bash
cd backend
python scripts/init_postgres.py
```

This script will:
- Create the `rag_vector` database
- Install the `vector` extension (pgvector)
- Attempt to install `zhparser` (Chinese tokenizer); fall back to `pg_trgm` if unavailable
- Create the `document_chunks` table along with HNSW vector indexes and GIN full-text indexes

### 4. Ingest Recipe Data

```bash
cd backend
python scripts/ingest_data.py
```

On first run, the `sentence-transformers` library will automatically download the `BAAI/bge-large-zh-v1.5` model (~1.2 GB) from Hugging Face. The script then parses Markdown files under `backend/data/`, chunks them, computes embeddings, and writes everything into PostgreSQL.

> **Already have the model locally?** If model files exist under `backend/models/embeddings/`, `embedding.py` will automatically detect and load them from the local path, skipping the network download.

### 5. Start Services

**Backend**:

```bash
cd backend
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
python run.py
```

Backend runs at http://localhost:5000

**Frontend**:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173

## Usage

1. Open http://localhost:5173, register an account, and log in
2. Navigate to the "Intelligent Q&A" page
3. Ask questions such as:
   - "How do I make Kung Pao Chicken?"
   - "Recommend some staple foods"
   - "Nutritional facts of old hen soup"
4. Watch the streaming status:
   - **Analyzing query intent...** → Independent model decides whether retrieval is needed
   - **Retrieving recipe information...** → Hybrid retrieval is executed (only appears when needed)
   - **Generating answer...** → Main model streams the final answer based on refined knowledge

### Custom Avatars (Optional)

Place images into the `frontend/public/avatars/` directory:
- `user.xxx` — User avatar
- `bot.xxx` — Assistant avatar

Any common format is supported (`.png` / `.jpg` / `.jpeg` / `.webp` / `.gif`); the component will auto-detect. If no image is present, a default gradient fallback is used.

## Common Issues and Solutions

### 1. Frontend reports "Network request failed" or CORS error

**Cause**: The frontend `.env` uses `http://localhost:5000/api` together with `withCredentials=true`, conflicting with backend CORS settings.

**Fix**: Set `VITE_API_BASE_URL=/api` in `frontend/.env` so the Vite proxy forwards requests to the backend.

### 2. psycopg2 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xd6` on Windows

**Cause**: On Chinese Windows, the psycopg2 C extension reads system environment variables (e.g. PATH, USERPROFILE) as UTF-8, but they are actually GBK-encoded.

**Fix** (choose one):
- **Option A**: Delete all `__pycache__` folders under `backend`, then restart the server
- **Option B**: Start the backend from PowerShell: `$env:PYTHONUTF8=1; python run.py`
- **Option C**: Ensure system environment variables do not contain Chinese paths, or explicitly set `PGCLIENTENCODING=utf8`

The code already sets `os.environ['PGCLIENTENCODING'] = 'utf8'` at the top of every file that imports psycopg2. If the error persists, try Option A or B first.

### 3. `init_postgres.py` reports `zhparser` installation failed

**Cause**: `zhparser` is a third-party PostgreSQL Chinese tokenizer extension. On Windows it usually requires manual compilation and is not present by default.

**Fix**: No action needed. The script automatically falls back to `pg_trgm` (trigram-based fuzzy matching). Retrieval will still work. For more precise Chinese tokenization, install `zhparser` manually and re-run the script.

### 4. `ingest_data.py` hangs on "Loading embedding model" for the first time

**Cause**: The first run of `sentence-transformers` downloads `BAAI/bge-large-zh-v1.5` (~1.2 GB) from Hugging Face.

**Fix**: Keep the network connection stable and wait for the download to complete. After caching locally, subsequent runs will not re-download. Cache locations:
- Windows: `C:\Users\%USERNAME%\.cache\torch\sentence_transformers`
- Linux/macOS: `~/.cache/torch/sentence_transformers`

### 5. Model exists locally but the runtime still tries to download from Hugging Face

**Cause**: `SentenceTransformer` attempts to connect to Hugging Face for metadata validation even when a local cache exists.

**Fix**: The code automatically detects local snapshot paths under `backend/models/embeddings/` and loads directly from the local path. If the issue persists, delete `backend/app/rag/__pycache__` and restart the backend.

### 6. Chat responds with "Service busy" or the LLM does not respond

**Troubleshooting**:
1. Verify `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` in `backend/.env` is correct
2. Ensure `LLM_PROVIDER` matches the configured key (`anthropic` or `openai`)
3. Check the backend console for specific error stack traces
4. Confirm PostgreSQL is running and the `rag_vector` database exists

### 7. Conversation history is lost after server restart

**Cause**: Sessions are stored in an in-memory dictionary (`_chat_sessions`) and are not persisted.

**Fix**: This is a known design choice in the current version. To persist sessions, store them in MySQL or Redis.

### 8. No search results returned

**Troubleshooting**:
1. Confirm `python scripts/ingest_data.py` has been executed and printed a success message with a non-zero record count
2. Check table contents via psql:
   ```bash
   psql -h localhost -p 5432 -U postgres -d rag_vector
   SELECT COUNT(*) FROM document_chunks;
   ```
3. Verify that `.md` files exist under `backend/data/`
