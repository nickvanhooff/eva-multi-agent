# Eva Multi-Agent System

Autonomous multi-agent marketing campaign generator built with **pure LangGraph** (no LangChain).

## Architecture

5 specialized agents collaborate to generate complete marketing campaigns:

| Agent | Role | Temperature |
|-------|------|-------------|
| Researcher | Product/market analysis | 0.4 |
| Strateeg | Strategy & positioning | 0.5 |
| Copywriter | Marketing copy | 0.9 |
| Social Specialist | Platform-specific content | 0.8 |
| Campaign Manager | Coordination & QA | 0.3 |

See [docs/architecture.md](docs/architecture.md) for detailed diagrams.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env         # Configure your LLM provider
python src/main.py
```

## Tech Stack

- **LangGraph** — Graph orchestration (StateGraph, conditional edges, checkpointing)
- **OpenAI SDK** — LLM calls (compatible with Ollama, OpenRouter, Groq)
- **No LangChain** — Pure LangGraph approach, LangChain integration planned for later
