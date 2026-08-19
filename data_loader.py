from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# 🔥 IMPORTANT: update dimension
EMBED_DIM = 384

CHUNK_SIZE = 700      # words per chunk (was llama-index's char-based splitter)
CHUNK_OVERLAP = 100   # words of overlap between chunks

bm25_index = None
chunk_corpus = []

# ✅ Embedding model, downloaded from Hugging Face Hub — loaded lazily, not at import time
model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return model


def preload_model():
    """Call this at FastAPI startup so the download/load happens once at
    container boot, not mid-request on the first /ingest or /query call."""
    get_model()


def build_bm25_index(chunks: list[str]):
    global bm25_index, chunk_corpus
    tokenized = [c.lower().split() for c in chunks]
    bm25_index = BM25Okapi(tokenized)
    chunk_corpus = chunks


def _split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap
    return chunks


def load_and_chunk_pdf(path: str) -> list[str]:
    reader = PdfReader(path)
    texts = [page.extract_text() or "" for page in reader.pages]

    chunks = []
    for t in texts:
        if t.strip():
            chunks.extend(_split_text(t))

    build_bm25_index(chunks)
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings = get_model().encode(texts)
    return embeddings.tolist()