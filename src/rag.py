"""RAG module — PDF ingestion, chunking, embedding, and retrieval.

Stack:
- PyMuPDF       : PDF parsing (local, no API)
- sentence-transformers/all-MiniLM-L6-v2 : embeddings (local, CPU, free)
- ChromaDB      : vector store (local, persistent-capable, swappable)
- LangChain     : glue layer (loaders, splitter, retriever)
"""

from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Embedding model — ~80 MB, runs on CPU, no API key required
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Chunk settings — characters (not words), ~10% overlap
# 800 chars ≈ 130 words ≈ 5-6 sentences — enough context for narrative/thematic text
CHUNK_SIZE = 800
CHUNK_OVERLAP = 80

# Number of chunks to retrieve per query
# Lower = less noise injected into the researcher prompt
TOP_K = 2

# Queries per campaign type — controls what the Researcher extracts from the PDF
_QUERIES: dict[str, list[str]] = {
    "product": [
        "Wat is het product en wat zijn de belangrijkste kenmerken en voordelen?",
        "Wie is de doelgroep van dit product?",
        "Wat zijn de unieke verkooppunten (USPs) van dit product?",
        "Wat is de merkidentiteit, tone of voice en positionering?",
        "Wat zijn de markt, concurrentie en kansen voor dit product?",
    ],
    "book": [
        "Wie is de auteur en wat is zijn of haar achtergrond, expertise of persoonlijke connectie met het onderwerp?",
        "Wat is het centrale thema, genre en de belofte van het boek aan de lezer?",
        "Welke historische, culturele of geografische context wordt beschreven in het boek?",
        "Wat maakt dit boek uniek ten opzichte van andere werken over hetzelfde onderwerp?",
        "Voor welke lezer is dit boek bedoeld en welke leeservaring biedt het (kennis, emotie, escapisme, verbinding)?",
    ],
}


def _build_vector_store(pdf_path: str) -> Chroma:
    """Load a PDF, chunk it, and store embeddings in ChromaDB."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    print(f"[RAG] Loading PDF: {path.name}")
    loader = PyMuPDFLoader(str(path))
    documents = loader.load()
    print(f"[RAG] Loaded {len(documents)} pages")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    print(f"[RAG] Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    print(f"[RAG] Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # in-memory ChromaDB — rebuilt each run (no persistent path needed per-run)
    vector_store = Chroma.from_documents(chunks, embeddings)
    print(f"[RAG] Vector store built ({len(chunks)} chunks indexed)")

    return vector_store


def retrieve_pdf_context(pdf_path: str, campaign_type: str = "product") -> str:
    """Run campaign-type-specific queries against the PDF and return combined context.

    This is the main entry point for the RAG node. It:
    1. Builds a vector store from the PDF
    2. Runs queries matching the campaign_type against the vector store
    3. Deduplicates retrieved chunks
    4. Returns a single formatted context string for the Researcher

    Args:
        pdf_path: Path to the PDF file.
        campaign_type: Controls which query set is used ("product" or "book").
                       Falls back to "product" for unknown types.

    Returns:
        A formatted string with all retrieved context passages.
    """
    queries = _QUERIES.get(campaign_type, _QUERIES["product"])
    print(f"[RAG] Using '{campaign_type}' queries ({len(queries)} total)")

    vector_store = _build_vector_store(pdf_path)
    retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K})

    seen = set()
    passages = []

    for query in queries:
        docs = retriever.invoke(query)
        for doc in docs:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                passages.append((query, doc.page_content))

    print(f"[RAG] Retrieved {len(passages)} unique passages across {len(queries)} queries")

    lines = ["=== PDF CONTEXT (via RAG) ===\n"]
    for query, passage in passages:
        lines.append(f"[Vraag: {query}]")
        lines.append(passage.strip())
        lines.append("")

    return "\n".join(lines)
