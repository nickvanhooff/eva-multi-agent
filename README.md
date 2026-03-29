# Eva Multi-Agent System

Autonomous multi-agent marketing campaign generator built with **pure LangGraph** (no LangChain).

## Architecture

5 specialized agents collaborate to generate complete marketing campaigns:

| Agent | Role | Skills | Tools | Temperature |
|-------|------|--------|-------|-------------|
| Researcher | Product/market analysis | `product-marketing-context`, `marketing-ideas` | DuckDuckGo search, Wikipedia | 0.4 |
| Strateeg | Strategy & positioning | `content-strategy`, `marketing-psychology` | — | 0.5 |
| Copywriter | Marketing copy | `copywriting`, `copy-editing` | — | 0.9 |
| Social Specialist | Platform-specific content | `social-content` | — | 0.8 |
| Campaign Manager | Coordination & QA | `launch-strategy` | — | 0.3 |

See [docs/architecture.md](docs/architecture.md) for detailed diagrams.
See [docs/rag.md](docs/rag.md) for the RAG implementation design (PDF ingestion, embeddings, vector store choices).

## Setup

### Docker (primary)

```bash
cp .env.example .env        # Configure your LLM provider (Groq/OpenRouter/Ollama)
docker compose build
docker compose up
```

Campaign reports are saved to `./campaigns/` on the host machine via volume mount.

To run once without keeping the container:

```bash
docker compose run --rm eva
```

### Local (development only)

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

## RAG — PDF input support

The Researcher agent can ingest a product PDF before it runs. A dedicated `pdf_ingestion` node runs first in the graph, extracts relevant passages via RAG, and injects them into the Researcher's prompt.

**Stack:**

| Component | Library | Purpose |
|---|---|---|
| PDF parser | `PyMuPDF` | Extract raw text from PDF (local, no API) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Convert text chunks to vectors (local CPU, free) |
| Vector store | `ChromaDB` | Store and search vectors by semantic similarity |
| Glue | `LangChain` | Loaders, splitter, retriever |

**How it works:**

```
PDF → PyMuPDF → chunks (500 words, 50 overlap) → embeddings → ChromaDB
                                                                     ↑
5 fixed campaign queries → similarity search → top 3 chunks each → pdf_context → Researcher prompt
```

The 5 fixed queries extract campaign-relevant information: product features, target audience, USPs, brand identity, and market positioning.

**Usage:**

```python
# Without PDF — works exactly as before
run_campaign("dubbele airfryer van Philips")

# With PDF — RAG runs automatically before the Researcher
run_campaign("dubbele airfryer van Philips", pdf_path="data/philips.pdf")
```

See [docs/rag.md](docs/rag.md) for full stack decisions and trade-offs.

## Tech Stack

- **LangGraph** — graph orchestration (StateGraph, conditional edges, checkpointing)
- **LangChain** — LLM wrapper (`ChatOpenAI`), required for LangSmith tracing
- **LangSmith** — observability: traces, token usage, latency per agent
- **OpenAI-compatible API** — works with Groq, OpenRouter, Ollama via `base_url`
- **DuckDuckGo + Wikipedia** — live tool data for Researcher agent (no API key)
- **Docker** — primary runtime, includes Ollama service for local LLM fallback
- **PyMuPDF + ChromaDB + sentence-transformers** — RAG pipeline for PDF input
