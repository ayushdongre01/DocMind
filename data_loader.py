from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# ✅ Local embedding model (FREE)
#model = SentenceTransformer("E:/DocMind/models/all-MiniLM-L6-v2")
model = SentenceTransformer("all-MiniLM-L6-v2")

# 🔥 IMPORTANT: update dimension
EMBED_DIM = 384

splitter = SentenceSplitter(chunk_size=700, chunk_overlap=100)
bm25_index = None
chunk_corpus = []

def build_bm25_index(chunks: list[str]):
    global bm25_index, chunk_corpus
    tokenized = [c.lower().split() for c in chunks]
    bm25_index = BM25Okapi(tokenized)
    chunk_corpus = chunks

def load_and_chunk_pdf(path: str):
    docs = PDFReader().load_data(file=path)
    texts = [d.text for d in docs if getattr(d, "text", None)]

    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))

    build_bm25_index(chunks)
    
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings = model.encode(texts)
    return embeddings.tolist()