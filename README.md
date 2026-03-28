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

## Tech Stack

- **LangGraph** — graph orchestration (StateGraph, conditional edges, checkpointing)
- **LangChain** — LLM wrapper (`ChatOpenAI`), required for LangSmith tracing
- **LangSmith** — observability: traces, token usage, latency per agent
- **OpenAI-compatible API** — works with Groq, OpenRouter, Ollama via `base_url`
- **DuckDuckGo + Wikipedia** — live tool data for Researcher agent (no API key)
- **Docker** — primary runtime, includes Ollama service for local LLM fallback
