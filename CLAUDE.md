# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG-based intelligent Q&A system for 老乡鸡 (a Chinese fast-food chain) recipes. Users ask questions about dishes, ingredients, nutrition, or recommendations.

**Core design principle**: The main conversation context is **never polluted by the retrieval process**. Intent analysis and knowledge refinement are handled by independent LLM instances; the main model only generates the final answer.

**Stack**: React 18 + TypeScript + Vite (frontend), Flask + Python (backend), MySQL (users), PostgreSQL + pgvector (RAG vectors).

## Common Commands

### Start Development

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py               # http://localhost:5000

# Terminal 2 — Frontend
cd frontend
npm install
cp .env.example .env        # VITE_API_BASE_URL=/api (Vite proxy)
npm run dev                 # http://localhost:5173
```

### Database Initialization

Two databases are required before the app works fully:

**MySQL** (users/auth):
```bash
cd backend
python init/create_database.py   # CREATE DATABASE IF NOT EXISTS
python init/create_tables.py     # SQLAlchemy create_all()
```

**PostgreSQL + pgvector** (RAG vectors):
```bash
cd backend
python scripts/init_postgres.py  # Creates DB, extensions, document_chunks table, indexes
python scripts/ingest_data.py    # Parses backend/data/ markdown → chunks → embeddings → PG
```

- `init_postgres.py` attempts to install `zhparser` for Chinese full-text search; if unavailable it falls back to `pg_trgm`.
- `ingest_data.py` `TRUNCATE`s the table on each run and re-ingests everything.

### Build

```bash
cd frontend
npm run build    # tsc && vite build
npm run preview  # Preview production build locally
```

No test suite is currently configured.

## High-Level Architecture

### Independent-Model RAG Flow

The system uses **three separate LLM instances** to keep the main dialogue history clean:

1. **`intent_analyzer.py`** — `IntentAnalyzer` (isolated LLM, temp=0.1, max_tokens=64). Analyzes the user query and returns a boolean indicating whether recipe retrieval is needed. Takes optional `history_text` for pronoun resolution.
2. **`search_pipeline.py`** — Orchestrates retrieval when intent analysis returns `True`:
   - `query_rewriter.py` rewrites the query into 1-3 retrieval-friendly queries (isolated LLM call, temp=0.2).
   - `hybrid_search.py` runs semantic + keyword search in parallel:
     - Semantic: `vector_store.py` → pgvector cosine similarity (BAAI/bge-large-zh-v1.5, 1024-dim).
     - Keyword: `fulltext_search.py` → zhparser Chinese FTS (or pg_trgm fallback).
     - Weighted fusion (vector 0.6 / keyword 0.4), title/category boost 1.1x.
   - Deduplicates across rewritten queries, returns top-5.
3. **`context_rewriter.py`** — `ContextRewriter` (isolated LLM, temp=0.3, max_tokens=1024). Refines raw retrieval results into concise, targeted knowledge material before injection into the main dialogue.

### Chat Flow (SSE Stream)

`backend/app/routes/chat.py` implements the main streaming endpoint:

1. Fetch in-memory session history; build `history_text` for independent models.
2. **Step 1**: `IntentAnalyzer.analyze(message, history_text)` → decides if retrieval is needed. SSE status: `thinking`.
3. **Step 2** (if needed): `SearchPipeline.search(message)` → raw results. SSE status: `calling_tool`.
4. **Step 3** (if needed): `ContextRewriter.rewrite(message, raw_context, history_text)` → refined knowledge.
5. **Step 4**: Build the main LLM message list from `SystemMessage` + clean `HumanMessage`/`AIMessage` history. The last user message is replaced with a composite prompt containing the refined knowledge + original question. Stream via `llm.stream()`. SSE status: `generating`.

**Key detail**: `chat.py` contains a defensive helper `_extract_text` because Anthropic models may return `content` as a list of blocks rather than a plain string. Do not remove this.

**Note**: `tools.py` still defines a `search_recipes` LangChain `@tool`, but the current chat flow no longer uses `bind_tools` or `ToolMessage`. The pipeline is invoked directly by `chat.py` instead.

### Auth Flow

- JWT (HS256, 30-day expiry) returned on login, stored in `localStorage`, sent as `Bearer` header.
- `@token_required` decorator guards routes; injects `g.current_user_id`.
- Flask-CORS is explicitly configured for `http://localhost:5173` and `http://127.0.0.1:5173` **only** — do not use `origins=*` with credentials.

### Frontend Proxy & API Base URL

In development, `frontend/.env` must set `VITE_API_BASE_URL=/api` so the Vite proxy handles routing to `localhost:5000`. Using the full URL (`http://localhost:5000/api`) combined with `withCredentials=true` causes a CORS credentials conflict.

## Important Environment Variables

Backend `.env` (copy from `.env.example`):
- `DATABASE_URI` — MySQL connection (e.g. `mysql+pymysql://root:123456@localhost:3306/rag_agent?charset=utf8mb4`)
- `VECTOR_DB_*` — PostgreSQL host/port/name/user/password
- `LLM_PROVIDER` — `anthropic` or `openai`
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` — Provider API keys
- `ANTHROPIC_MODEL` / `OPENAI_MODEL` — Model names
- `SECRET_KEY` — Flask secret key
- `EMBEDDING_MODEL` — Default `BAAI/bge-large-zh-v1.5`
- `EMBEDDING_DEVICE` — `cpu` or `cuda`

Frontend `.env`:
- `VITE_API_BASE_URL` — Must be `/api` in dev (uses Vite proxy)

## Notable Constraints

- **Session storage is in-memory only** (`_chat_sessions: dict` in `llm_service.py`). Sessions are lost on server restart.
- **Windows encoding workaround**: Multiple backend files set `os.environ['PGCLIENTENCODING'] = 'utf8'` and pass `client_encoding='utf8'` to psycopg2 to avoid `UnicodeDecodeError` on Chinese Windows systems. Preserve these when adding new files that import psycopg2.
- **Data source**: Recipe markdowns live in `backend/data/` organized by category folders (主食, 炒菜, 汤, etc.). The ingest pipeline parses these directly; there is no `recipes.json`.
