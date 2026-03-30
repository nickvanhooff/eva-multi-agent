# Eva Multi-Agent System

Autonomous multi-agent marketing campaign generator built with **LangGraph**. Generates complete campaigns — strategy, copy, social content, and image — via a pipeline of 7 specialized agents. Exposed via a **FastAPI backend** and a **React+Vite dashboard**.

## Architecture

7 nodes in a sequential pipeline with conditional feedback loops from the Campaign Manager:

```
PDF Ingestion → Researcher → Strateeg → Copywriter → Social Specialist → Campaign Manager → Image Generator
                                              ↑________________↑
                                           (feedback loop — max 3x)
```

| Node | Role | Model | Temperature |
|------|------|-------|-------------|
| PDF Ingestion | RAG — extracts context from PDF | — | — |
| Researcher | Market & context analysis | llama-3.1-8b (Groq) | 0.4 |
| Strateeg | Strategy & positioning | llama-3.1-8b (Groq) | 0.5 |
| Copywriter | Marketing copy | llama-3.3-70b (Groq) | 0.9 |
| Social Specialist | Platform-specific content | llama-3.3-70b (Groq) | 0.8 |
| Campaign Manager | QA — approves or requests revision | llama-3.3-70b (Groq) | 0.3 |
| Image Generator | Campaign visual via SDXL (GPU) | SDXL-Turbo | — |

Skills are loaded dynamically at runtime based on `campaign_type`. See [docs/architecture.md](docs/architecture.md) for full diagrams and state schema.

## Setup

### Docker (primary)

```bash
cp .env.example .env        # set API keys (see .env.example)
docker compose build
docker compose up
```

The API runs at `http://localhost:8000`. Campaign reports are saved to `./campaigns/` via volume mount.

### Local development

**API:**
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend (separate terminal):**
```bash
cd frontend
npm install
npm run dev                 # runs at http://localhost:5173
```

The Vite dev server proxies `/api` → `http://localhost:8000` automatically.

## API

FastAPI backend at port 8000. Full docs at `http://localhost:8000/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/campaigns` | Start a campaign — returns `job_id` |
| `GET` | `/campaigns/{id}` | Poll status + result |
| `GET` | `/campaigns/{id}/stream` | SSE stream — real-time agent events |
| `GET` | `/campaigns/{id}/events` | All events for a job (live or from file) |
| `GET` | `/campaigns` | List all saved campaign reports |
| `GET` | `/pdfs` | List available PDFs in `data/` |
| `POST` | `/pdfs/upload` | Upload a PDF |
| `GET` | `/static/...` | Serve campaign images |

### Start a campaign

```bash
curl -X POST http://localhost:8000/campaigns \
  -H "Content-Type: application/json" \
  -d '{"product_description": "Philips Airfryer XL", "campaign_type": "product"}'
# → {"job_id": "..."}

curl http://localhost:8000/campaigns/{job_id}
# → {"status": "done", "result": {...}}
```

### Stream agent events (SSE)

Each agent call emits two events via Server-Sent Events:
- `llm_call` — system prompt + user prompt sent to the model
- `llm_response` — raw response received
- `node_done` — node completed with state update

Events are also saved to `campaigns/{report_name}_events.json` for later review.

## Frontend

React+Vite dashboard at `http://localhost:5173`.

| Route | Screen |
|-------|--------|
| `/` | Dashboard — stats, pipeline overview, recent campaigns |
| `/campaigns/new` | New Campaign — type toggle, description, PDF upload |
| `/campaigns/:id/live` | Live view — real-time pipeline + agent activity log |
| `/campaigns/:id` | Results — Strategy / Copy / Social / Image / Logs tabs |
| `/history` | Campaign History — filterable table |

## RAG — PDF context

The `pdf_ingestion` node runs before the Researcher. It extracts relevant passages from a PDF and injects them into the Researcher's prompt.

**Stack:**

| Component | Library |
|-----------|---------|
| PDF parser | PyMuPDF |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector store | ChromaDB |
| Splitter | LangChain RecursiveCharacterTextSplitter |

**Chunking:** 800 characters, 80 overlap, TOP_K=2 per query.

**Queries are campaign-type-specific** — book campaigns use narrative queries (author, themes, audience), product campaigns use conversion queries (USPs, market, features).

See [docs/rag.md](docs/rag.md) for full stack decisions.

## Campaign types

`campaign_type` controls which skill Markdown files are injected per agent:

| Agent | `product` | `book` |
|-------|-----------|--------|
| Researcher | `research-brief` | `book-context` |
| Copywriter | `copywriting` | `book-copywriting` |
| Social Specialist | `social-media` | `book-social` |
| Campaign Manager | `launch-strategy` | `book-launch-strategy` |

Adding a new type: add skill files to `src/skills/` and an entry to `SKILL_MAP` in `skills_config.py`.

## Observability

**LangSmith** traces all LLM calls when enabled:

```env
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=<key>
LANGSMITH_PROJECT=eva-multi-agent
```

Traces include per-agent latency, token usage, and full message history. Dashboard: https://smith.langchain.com/

## Key files

```
src/
├── api.py              FastAPI app — all endpoints + SSE streaming
├── graph.py            LangGraph StateGraph assembly
├── state.py            CampaignState TypedDict
├── main.py             run_campaign() entry point + report saving
├── llm.py              Provider-agnostic LLM wrapper (Groq/OpenRouter/Ollama)
├── rag.py              PDF ingestion pipeline
├── event_bus.py        Thread-local event bus for agent logging
├── tracing.py          LangSmith setup
├── agents/             One file per agent node
└── skills/             Markdown skill files + SKILL_MAP config

frontend/
├── src/api.js          Fetch wrapper + SSE helper
├── src/App.jsx         Router
├── src/pages/          5 pages
└── src/components/     Sidebar, AgentPipeline
```

## Tech Stack

- **LangGraph** — graph orchestration (StateGraph, conditional edges, MemorySaver)
- **LangChain** — LLM wrapper (ChatOpenAI), text splitter, RAG loaders
- **LangSmith** — observability: traces, token usage, latency per agent
- **FastAPI + uvicorn** — REST API + SSE streaming
- **React + Vite** — dashboard frontend
- **Groq / OpenRouter / Ollama** — LLM providers via OpenAI-compatible API
- **PyMuPDF + ChromaDB + sentence-transformers** — RAG pipeline
- **Stable Diffusion XL (SDXL-Turbo)** — local image generation via GPU
- **Docker** — primary runtime with Ollama sidecar for local LLM fallback
