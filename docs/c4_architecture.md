# C4 Architecture Diagrams — Eva Multi-Agent

Three levels of the [C4 model](https://c4model.com) for the Eva multi-agent marketing campaign generator.

---

## Level 1 — System Context

> Who uses Eva and which external systems does it depend on?

```mermaid
C4Context
  title System Context — Eva Multi-Agent Marketing System
  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")

  Person(marketeer, "Marketing Professional", "Submits product description + optional PDF, receives a complete marketing campaign")

  System(eva, "Eva Multi-Agent System", "Multi-agent pipeline: research, strategy, copy, social content, campaign image")

  System_Ext(groq, "Groq API", "Cloud LLM — Llama 3.1-8B and 3.3-70B")
  System_Ext(openrouter, "OpenRouter API", "Fallback cloud LLM — Llama 3.3-70B free tier")
  System_Ext(ollama, "Ollama", "Self-hosted local LLM via Docker")

  System_Ext(hf, "Hugging Face Hub", "all-MiniLM-L6-v2 embeddings and SDXL-Turbo image model weights")
  System_Ext(duckduckgo, "DuckDuckGo", "Web search for real-time market analysis")
  System_Ext(wikipedia, "Wikipedia", "Background knowledge lookups by Researcher")

  System_Ext(langsmith, "LangSmith", "Optional tracing and run monitoring")

  Rel(marketeer, eva, "Product description + PDF", "HTTP REST / SSE")
  Rel(eva, groq, "LLM inference", "HTTPS")
  Rel(eva, openrouter, "LLM inference (fallback)", "HTTPS")
  Rel(eva, ollama, "LLM inference (local)", "HTTP")
  Rel(eva, hf, "Model downloads on first run", "HTTPS")
  Rel(eva, duckduckgo, "Market research queries", "HTTPS")
  Rel(eva, wikipedia, "Knowledge lookups", "HTTPS")
  Rel(eva, langsmith, "Agent traces (when enabled)", "HTTPS")
```

---

## Level 2 — Container

Split into two views to keep each diagram readable.

### 2a — Runtime and Request Flow

> How does a campaign request travel through the system?

```mermaid
C4Container
  title Container Diagram — Runtime and Request Flow
  UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")

  Person(marketeer, "Marketing Professional", "Creates campaigns via the web dashboard")

  System_Boundary(eva_sys, "Eva Multi-Agent System") {
    Container(frontend, "Web Dashboard", "React + Vite", "5-page SPA: New Campaign, Live pipeline view, Results (6 tabs), History")
    Container(api, "Eva API", "FastAPI", "REST endpoints and SSE streaming. Manages jobs, PDF uploads, interrupt-resume")
    Container(pipeline, "Agent Pipeline", "LangGraph StateGraph", "8-node graph with conditional feedback loop. Runs as background thread per job")
    Container(ollama_c, "Ollama", "Docker container", "Serves local Llama models via OpenAI-compatible API on port 11434")
  }

  System_Ext(groq, "Groq API", "Cloud LLM — Llama 3.1-8B / 3.3-70B")
  System_Ext(openrouter, "OpenRouter", "Fallback cloud LLM")

  Rel(marketeer, frontend, "Uses", "Browser")
  Rel(frontend, api, "POST /campaigns, GET /stream, GET /results", "HTTP")
  Rel(api, pipeline, "Starts graph.stream() as background task")
  Rel(pipeline, groq, "Per-agent LLM calls", "HTTPS / OpenAI API")
  Rel(pipeline, openrouter, "LLM calls (fallback)", "HTTPS / OpenAI API")
  Rel(pipeline, ollama_c, "LLM calls (local provider)", "HTTP / OpenAI API")
```

### 2b — Data and Model Dependencies

> Which container reads and writes what data, and which external services supply models?

```mermaid
C4Container
  title Container Diagram — Data and Model Dependencies
  UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")

  System_Boundary(eva_sys, "Eva Multi-Agent System") {
    Container(pipeline, "Agent Pipeline", "LangGraph", "Researcher searches the web; Image Generator produces visuals; results saved as JSON")
    Container(rag, "RAG Module", "PyMuPDF + ChromaDB + HF Embeddings", "Ingests uploaded PDFs: parse, chunk, embed, query, return passages")
    ContainerDb(fs, "Filesystem", "Docker Volume", "data/ for uploaded PDFs. campaigns/ for JSON reports and generated images")
  }

  System_Ext(hf, "Hugging Face Hub", "all-MiniLM-L6-v2 embeddings and SDXL-Turbo image model")
  System_Ext(duckduckgo, "DuckDuckGo", "Web search")
  System_Ext(wikipedia, "Wikipedia", "Knowledge lookups")
  System_Ext(langsmith, "LangSmith", "Optional run traces")

  Rel(pipeline, rag, "PDF Ingestion node: retrieve_pdf_context(pdf_path)")
  Rel(rag, hf, "Downloads all-MiniLM-L6-v2 on first run", "HTTPS")
  Rel(rag, fs, "Reads PDF from data/")
  Rel(pipeline, hf, "Downloads SDXL-Turbo weights on first run", "HTTPS")
  Rel(pipeline, fs, "Writes campaign JSON and PNG to campaigns/")
  Rel(pipeline, duckduckgo, "Researcher: market analysis queries", "HTTPS")
  Rel(pipeline, wikipedia, "Researcher: background lookups", "HTTPS")
  Rel(pipeline, langsmith, "Traces when LANGSMITH_ENABLED=true", "HTTPS")
```

---

## Level 3 — Component

Split into two views: the agent pipeline and the shared infrastructure.

### 3a — Agent Pipeline

> What are the 8 agent nodes and what data flows between them?

```mermaid
C4Component
  title Component Diagram — Agent Pipeline Nodes
  UpdateLayoutConfig($c4ShapeInRow="1", $c4BoundaryInRow="1")

  Container_Boundary(pipeline_b, "Agent Pipeline (LangGraph StateGraph)") {
    Component(pdf_node, "PDF Ingestion", "Python node", "Calls RAG module with pdf_path and campaign_type. Writes pdf_context and pdf_sources to state")
    Component(mismatch, "Mismatch Check", "LLM node — Llama 3.1-8B", "Validates product description matches PDF. Can pause graph via interrupt() for human confirmation")
    Component(researcher, "Researcher", "LLM node — Llama 3.1-8B", "Produces market_research and target_audience. Uses DuckDuckGo + Wikipedia for live data")
    Component(strategist, "Strategist", "LLM node — Llama 3.1-8B", "Produces strategy, positioning, and tone_of_voice from researcher output")
    Component(copywriter, "Copywriter", "LLM node — Llama 3.3-70B", "Writes copy_draft. Re-runs when Campaign Manager returns phase=copy_review")
    Component(social, "Social Specialist", "LLM node — Llama 3.3-70B", "Writes social_content per platform. Re-runs when Campaign Manager returns phase=social_review")
    Component(cm, "Campaign Manager", "LLM node + router — Llama 3.3-70B", "Evaluates copy + social against strategy. GOEDGEKEURD routes to Image Generator. AFGEWEZEN loops back (max 3 iterations)")
    Component(image_gen, "Image Generator", "SDXL-Turbo / GPU", "Generates PNG campaign visual from product description + positioning. Runs last after approval")
  }

  Rel_D(pdf_node, mismatch, "pdf_context, pdf_sources")
  Rel_D(mismatch, researcher, "product_description")
  Rel_D(researcher, strategist, "market_research, target_audience")
  Rel_D(strategist, copywriter, "strategy, positioning, tone_of_voice")
  Rel_D(copywriter, social, "copy_draft")
  Rel_D(social, cm, "social_content")
  Rel_D(cm, image_gen, "approved or max iterations reached")
```

#### Campaign Manager Routing Logic

> The only node with conditional outgoing edges — shown separately to avoid crossing lines.

```mermaid
flowchart TD
  CM["Campaign Manager"]

  CM -->|"GOEDGEKEURD / max iterations"| IG["Image Generator → END"]
  CM -->|"AFGEWEZEN — copy_review"| CW["Copywriter"]
  CM -->|"AFGEWEZEN — social_review"| SS["Social Specialist"]

  CW --> SS2["Social Specialist"]
  SS2 --> CM
  SS --> CM

  style CM fill:#1168BD,color:#fff
  style IG fill:#23a045,color:#fff
  style CW fill:#555,color:#fff
  style SS fill:#555,color:#fff
  style SS2 fill:#555,color:#fff
```

### 3b — Infrastructure Components

> How do agents share the LLM wrapper, event bus, RAG module, skills, and tracing?

```mermaid
C4Component
  title Component Diagram — Shared Infrastructure
  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")

  Container_Boundary(infra_b, "Eva Infrastructure (same process as Agent Pipeline)") {
    Component(rest_api, "REST API", "FastAPI", "Routes HTTP requests. Reads Event Bus to stream SSE to frontend. Handles interrupt-resume")
    Component(event_bus, "Event Bus", "Python in-memory dict", "Thread-local pub/sub. Agents push llm_call and node_done events. REST API reads them for SSE")
    Component(llm_wrapper, "LLM Wrapper", "LangChain ChatOpenAI", "Single call_llm() used by all 6 LLM nodes. Routes to Groq, OpenRouter, or Ollama per AGENT_LLM_CONFIG")
    Component(rag_module, "RAG Module", "PyMuPDF + ChromaDB + HF", "PDF Ingestion node calls this. Chunks PDF, embeds with all-MiniLM-L6-v2, queries ChromaDB, deduplicates results")
    Component(skills, "Skills System", "Markdown files", "get_skills(campaign_type, agent) returns Markdown prompt extension. Prepended to system prompt at runtime")
    Component(tracing, "Tracing", "LangSmith SDK", "setup_tracing() sets env vars. All LangChain calls auto-traced when LANGSMITH_ENABLED=true")
  }

  Container_Ext(groq_api, "Groq API", "Cloud LLM")
  Container_Ext(ollama, "Ollama", "Local LLM")
  Container_Ext(hf_hub, "Hugging Face Hub", "Embedding model weights")
  Container_Ext(langsmith_ext, "LangSmith", "Tracing SaaS")
  ContainerDb(fs, "Filesystem", "Docker Volume")

  Rel(llm_wrapper, groq_api, "HTTPS / OpenAI API")
  Rel(llm_wrapper, ollama, "HTTP / OpenAI API")
  Rel(llm_wrapper, event_bus, "Pushes llm_call and llm_response events")
  Rel(rest_api, event_bus, "Reads events for SSE response")
  Rel(rag_module, hf_hub, "Downloads all-MiniLM-L6-v2 on first run")
  Rel(rag_module, fs, "Reads PDF files from data/")
  Rel(rest_api, fs, "Writes campaign reports to campaigns/")
  Rel(tracing, langsmith_ext, "Streams run traces")
```

---

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Orchestration | LangGraph StateGraph | Typed state, conditional edges, MemorySaver checkpointing |
| LLM abstraction | LangChain ChatOpenAI + base_url | One interface for Groq, OpenRouter, Ollama — no code changes per provider |
| Per-agent models | 8B for research/strategy, 70B for creative/review | Cost-quality tradeoff per task |
| Embeddings | all-MiniLM-L6-v2, local CPU | Free, ~80 MB, no API key, good retrieval quality |
| Vector store | ChromaDB in-memory | No infra, rebuilt per run, swappable |
| Event streaming | SSE over in-memory Event Bus | Decouples agent logic from transport layer |
| Image generation | SDXL-Turbo, local GPU | No API cost, fp16 for speed, same container |
| Human-in-the-loop | LangGraph interrupt() | Native pause/resume, no custom state machine needed |
