# RAG — Retrieval-Augmented Generation in Eva

This document explains what RAG is, why it is used, how it works step by step, and which implementation choices were made for Eva.

---

## What is RAG?

RAG (Retrieval-Augmented Generation) is a technique where an LLM searches an external knowledge source before generating an answer. Instead of dumping an entire document into the prompt, only the relevant pieces are retrieved and passed to the model.

**Sources:**

- Lewis et al. (2020) — original RAG paper: `arxiv.org/abs/2005.11401`
- LangChain RAG conceptual overview: `python.langchain.com/docs/concepts/rag`

---

## Why RAG? The problem it solves

Every LLM has a context window — a hard limit on how much text it can process at once. GPT-4 supports ~~128,000 tokens (~~100 pages). A 200-page product PDF does not fit. And even if it did, LLMs lose focus when context is very long.

This is documented in the "Lost in the Middle" paper (`arxiv.org/abs/2307.03172`), which shows that LLMs forget information positioned in the middle of long prompts. RAG avoids this by only retrieving the 3–5 most relevant chunks per query.

**Sources:**

- "Lost in the Middle" — Liu et al. (2023): `arxiv.org/abs/2307.03172`
- OpenAI context window documentation: `platform.openai.com/docs/models`

---

## How RAG works — step by step

```
PDF → Chunks → Embeddings → Vector Store
                                   ↑
Query → Embedding → Search → Relevant chunks → LLM → Answer
```

### Step 1: Chunking

The PDF is split into small text segments. The overlap ensures that information spanning a chunk boundary is not lost.

- **Chunk size:** measured in **characters**, not words. 800 characters ≈ 130 words ≈ 5–6 sentences. For narrative text (books, articles) this is large enough to preserve context per passage.
- **Overlap:** 10% of chunk_size — 80 characters. Standard practice to prevent information loss at boundaries.

Eva uses `chunk_size=800, chunk_overlap=80`. An earlier setting of 500/50 was found to fragment narrative book text too aggressively, and the high `TOP_K` injected too much noise into the researcher prompt.

**Source:** Pinecone chunking strategies guide: `pinecone.io/learn/chunking-strategies`

### Step 2: Embeddings

Each chunk is converted to a vector — a list of numbers representing the *meaning* of the text. "Cheap product" and "low price" end up close together in this vector space, even though the words differ. This enables semantic search rather than keyword matching.

**Source:** Sentence Transformers documentation: `sbert.net`

### Step 3: Vector store

All vectors are stored in a database that can search by similarity — not exact word match, but meaning. At query time this makes retrieval very fast.

### Step 4: Query

The Researcher agent asks a question, e.g. "What is the target audience for this product?". That question is also converted to a vector using the same embedding model.

### Step 5: Retrieval

The vector store finds the 3–5 chunks whose vectors are closest to the query vector. These are the most semantically relevant pieces of the document.

### Step 6: Generation

The retrieved chunks + the query are passed to the LLM. It generates an answer based only on those specific passages from the PDF, not from general training data.

**Source:** LangChain RAG how-to: `python.langchain.com/docs/concepts/rag`

---

## Implementation decisions — three layers

### Layer 1: PDF parser

The first layer is reading the PDF and extracting raw text.


| Option         | What it does                   | Pro                                  | Con                          | Docker      | Why chosen / rejected                                                                            |
| -------------- | ------------------------------ | ------------------------------------ | ---------------------------- | ----------- | ------------------------------------------------------------------------------------------------ |
| **PyMuPDF**    | Fast, pure text extraction     | Free, lightweight, no extra deps     | No table / image support     | ✅ Works     | **Chosen** — minimal Docker image, no network required, sufficient for text-based marketing PDFs |
| **pdfplumber** | Better layout recognition      | Tables work better                   | Slightly slower, more memory | ✅ Works     | Alternative if the PDF contains tables or complex layouts                                        |
| **LlamaParse** | Cloud API, intelligent parsing | Very accurate, understands structure | Paid, requires internet      | ❌ Not local | Rejected — external API, does not fit the local/Docker constraint                                |


**Decision:** PyMuPDF — free, local, Docker-compatible, and marketing PDFs are text-based so table support is not needed.

**Sources:**

- PyMuPDF official docs: `pymupdf.readthedocs.io`
- pdfplumber GitHub: `github.com/jsvine/pdfplumber`
- LangChain PDF loaders: `python.langchain.com/docs/how_to/document_loader_pdf`

---

### Layer 2: Embeddings

The second layer converts text chunks into vectors.


| Option                    | Model                    | Local?   | Cost                 | Speed                           | Docker                 | Why chosen / rejected                                                         |
| ------------------------- | ------------------------ | -------- | -------------------- | ------------------------------- | ---------------------- | ----------------------------------------------------------------------------- |
| **sentence-transformers** | `all-MiniLM-L6-v2`       | Yes      | Free                 | Fast on CPU                     | ✅ Works                | **Chosen** — ~80 MB model, no GPU required, ideal for Docker on a laptop      |
| **sentence-transformers** | `all-mpnet-base-v2`      | Yes      | Free                 | Slightly slower, better quality | ✅ Works                | Alternative if accuracy matters more than speed                               |
| **OpenAI**                | `text-embedding-3-small` | No (API) | ~$0.02 per 1M tokens | Very fast                       | ✅ Works (via internet) | Fallback option if local embeddings are too slow — minimal cost for 200 pages |
| **Ollama**                | `nomic-embed-text`       | Yes      | Free                 | Medium                          | ✅ Works                | Alternative if Ollama is already running in Docker; adds a service dependency |


**Decision:** `sentence-transformers/all-MiniLM-L6-v2` — runs locally on CPU in Docker, fast enough for a 200-page PDF, completely free. Switch to OpenAI API if it proves too slow.

**Sources:**

- Sentence Transformers official site: `sbert.net`
- all-MiniLM-L6-v2 model card: `huggingface.co/sentence-transformers/all-MiniLM-L6-v2`
- all-mpnet-base-v2 model card: `huggingface.co/sentence-transformers/all-mpnet-base-v2`
- OpenAI embeddings docs and pricing: `platform.openai.com/docs/guides/embeddings`
- Ollama nomic-embed-text: `ollama.com/library/nomic-embed-text`

---

### Layer 3: Vector store

The third layer stores the vectors and handles similarity search.


| Option       | Type              | Persistent?              | Local? | Complexity    | Docker                     | Why chosen / rejected                                                             |
| ------------ | ----------------- | ------------------------ | ------ | ------------- | -------------------------- | --------------------------------------------------------------------------------- |
| **FAISS**    | In-memory / file  | Optional (`.index` file) | Yes    | Low           | ✅ Works                    | Simple option — no server needed, works as a file inside the container            |
| **ChromaDB** | Local database    | Yes by default           | Yes    | Medium        | ✅ Works                    | **Chosen** — cleaner API, persistent out of the box, easy to swap for cloud later |
| **Qdrant**   | Local or cloud DB | Yes                      | Yes    | Medium-high   | ✅ Works (own Docker image) | Powerful but requires a separate Docker service — overkill for this project       |
| **Pinecone** | Cloud only        | Yes                      | No     | Low (managed) | ❌ Not local                | Rejected — cloud-only, does not fit the local constraint                          |
| **Weaviate** | Local or cloud    | Yes                      | Yes    | High          | ✅ Works (own Docker image) | Too complex for this use case — better suited for large enterprise systems        |


**Decision:** ChromaDB.

- FAISS is slightly simpler but has weaker LangChain integration docs.
- ChromaDB has a cleaner API, works persistently by default, and can later be swapped for Qdrant or Pinecone without changing the retrieval logic.

---

### Why not PostgreSQL (+ pgvector)?

PostgreSQL is a relational database — it stores rows and columns and searches on exact values (IDs, strings, dates). It does not understand meaning.

With the `pgvector` extension, PostgreSQL can also store vectors and run similarity search:

```sql
SELECT * FROM chunks ORDER BY embedding <=> query_embedding LIMIT 5;
```

This works, but PostgreSQL is the wrong tool for a RAG-only use case:

| | ChromaDB | PostgreSQL + pgvector |
|---|---|---|
| Setup | `pip install chromadb`, starts in-process | Separate Postgres container + pgvector extension |
| Docker | ✅ No extra service | ✅ But requires its own container |
| Vector search | ✅ Native — built for this | ⚠️ Bolt-on extension, not the primary purpose |
| Relations / joins | ❌ Not for | ✅ Yes — full SQL queries |
| Persistent | ✅ Out of the box | ✅ Out of the box |
| Complexity for this project | Low | Medium-high |
| Added value for RAG-only | ❌ None | ❌ None — only useful when other data (users, history) also lives in the DB |

**PostgreSQL becomes relevant when Eva grows** — for example, storing campaign history, user profiles, or client data in the same database. At that point, adding pgvector means vector search and relational data live in one place.

**Right now, Eva stores campaigns as JSON files and has no relational data.** PostgreSQL adds infrastructure complexity without any benefit. ChromaDB does exactly what is needed — nothing more.

**Sources:**

- FAISS GitHub (Meta Research): `github.com/facebookresearch/faiss`
- FAISS in LangChain: `python.langchain.com/docs/integrations/vectorstores/faiss`
- ChromaDB official docs: `docs.trychroma.com`
- ChromaDB in LangChain: `python.langchain.com/docs/integrations/vectorstores/chroma`
- Qdrant docs: `qdrant.tech/documentation`
- pgvector GitHub: `github.com/pgvector/pgvector`

---

## Chosen stack

```
PyMuPDF                              → PDF parsing (local, Docker-compatible)
sentence-transformers/all-MiniLM     → Embeddings (local, CPU, free)
ChromaDB                             → Vector store (local, persistent, swappable)
LangChain                            → Glue layer (already in Eva's stack)
```

**Why this combination:**

- Everything runs locally in Docker — no external services required
- Fits the existing LangChain/LangGraph stack — minimal changes
- Low entry barrier — all four have good documentation and many examples
- ChromaDB is easy to swap for Qdrant or Pinecone (cloud) later
- Fully free — no API costs for embeddings or storage

**Full stack reference:**

- LangGraph RAG tutorial (directly applicable to Eva): `langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag`

---

## What changed in Eva

These changes were made to add RAG to the existing system:

1. **New input fields:** `pdf_path` (optional PDF) and `campaign_type` (`"product"` or `"book"`) added to `CampaignState`
2. **New node before the Researcher:** `pdf_ingestion_node` in `graph.py` — runs RAG, writes `pdf_context` to state
3. **Campaign-type-specific queries:** `rag.py` uses different query sets per `campaign_type` — book queries ask about author, theme, cultural context; product queries ask about USPs, market, features
4. **Researcher reads `pdf_context`:** injected into the researcher prompt when available
5. **Other agents unchanged** — they work with the Researcher's output as before

### `CampaignState` (current)

```python
class CampaignState(TypedDict):
    # --- Input ---
    product_description: str
    campaign_type: str               # "product" | "book"
    pdf_path: Optional[str]          # optional path to PDF

    # --- RAG context ---
    pdf_context: str                 # retrieved chunks from ChromaDB

    # ... rest of fields unchanged
```

### Query sets per campaign type

| campaign_type | Queries focus on |
|---|---|
| `product` | Features/benefits, target audience, USPs, brand identity, market/competition |
| `book` | Author background, theme/genre, historical/cultural context, uniqueness, reading experience |

Using the wrong query set against a PDF causes the LLM to hallucinate — if you ask "what are the USPs?" against a book PDF, the model finds nothing and invents an answer.

---

## Docker compatibility summary


| Component             | Docker | Notes                                                           |
| --------------------- | ------ | --------------------------------------------------------------- |
| PyMuPDF               | ✅      | `pip install pymupdf` — no system deps                          |
| sentence-transformers | ✅      | Downloads model on first run; cache via volume mount            |
| ChromaDB              | ✅      | `pip install chromadb` — runs in-process, no separate container |
| FAISS (alternative)   | ✅      | `pip install faiss-cpu` — CPU-only build                        |
| Qdrant (alternative)  | ✅      | Requires `qdrant/qdrant` Docker image as separate service       |
| LlamaParse (rejected) | ❌      | Cloud API — not usable without internet in Docker               |
| Pinecone (rejected)   | ❌      | Cloud-only — not usable in isolated Docker environment          |


