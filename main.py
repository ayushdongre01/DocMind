import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
from dotenv import load_dotenv
import uuid
import os
import datetime
import base64
import tempfile
from openai import OpenAI
from io import BytesIO
from data_loader import load_and_chunk_pdf, embed_texts
from vector_db import QdrantStorage
from custom_types import RAGSearchResult, RAGUpsertResult, RAGChunkAndSrc

import data_loader
load_dotenv()

from pydantic import BaseModel

app = FastAPI()
class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    source: str

from fastapi import UploadFile, File

@app.post("/ingest")
async def ingest_pdf(file: UploadFile = File(...)):

    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    chunks = load_and_chunk_pdf(tmp_path)

    vecs = embed_texts(chunks)

    ids = [str(uuid.uuid4()) for _ in chunks]

    payloads = [{"source": file.filename, "text": c} for c in chunks]

    QdrantStorage().upsert(ids, vecs, payloads)

    return {"ingested": len(chunks)}

@app.post("/query")
async def query(req: QueryRequest):

    question = req.question
    top_k = req.top_k

    # Dense search
    query_vec = embed_texts([question])[0]
    store = QdrantStorage()
    dense_results = store.search(query_vec, top_k * 5)

    dense_contexts = []
    sources = []

    for ctx, src in zip(dense_results["contexts"], dense_results["sources"]):
        if src == req.source:
            dense_contexts.append(ctx)
            sources.append(src)

    dense_contexts = dense_contexts[:top_k]

    # Sparse search (BM25)
    sparse_contexts = []
    if data_loader.bm25_index:
        scores = data_loader.bm25_index.get_scores(question.lower().split())
        ranked = sorted(
            zip(data_loader.chunk_corpus, scores),
            key=lambda x: x[1],
            reverse=True
        )
        sparse_contexts = [c for c, _ in ranked[:top_k]]

    combined = list(dict.fromkeys(dense_contexts + sparse_contexts))

    context_block = "\n\n".join(f"- {c}" for c in combined[:top_k])

    user_content = (
        "Use the following context to answer the question.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n"
        "Answer concisely using ONLY the context above."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You answer questions using only the provided context."},
            {"role": "user", "content": user_content}
        ],
        max_tokens=512,
        temperature=0.2
    )

    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "sources": list(set(sources)),
        "num_contexts": len(combined)
    }


# ✅ GitHub Models Client (IMPORTANT)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://models.inference.ai.azure.com",
    timeout=30  # 🔥 prevents hanging
)

inngest_client = inngest.Inngest(
    app_id="rag_app",
    logger=logging.getLogger("uvicorn"),
    # is_production=False,
    is_production=True,
    serializer=inngest.PydanticSerializer()
)


# =========================
# 📥 INGEST FUNCTION
# =========================
@inngest_client.create_function(
    fn_id="RAG: Ingest PDF",
    trigger=inngest.TriggerEvent(event="rag/ingest_pdf"),
    throttle=inngest.Throttle(limit=2, period=datetime.timedelta(minutes=1)),
    rate_limit=inngest.RateLimit(
        limit=1,
        period=datetime.timedelta(hours=4),
        key="event.data.source_id",
    ),
)
async def rag_ingest_pdf(ctx: inngest.Context):

    def _load(ctx: inngest.Context) -> RAGChunkAndSrc:
        pdf_base64 = ctx.event.data["pdf_bytes"]
        source_id = ctx.event.data["source_id"]

        pdf_bytes = base64.b64decode(pdf_base64)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        chunks = load_and_chunk_pdf(tmp_path)

        return RAGChunkAndSrc(chunks=chunks, source_id=source_id)

    def _upsert(chunks_and_src: RAGChunkAndSrc) -> RAGUpsertResult:
        chunks = chunks_and_src.chunks
        source_id = chunks_and_src.source_id

        vecs = embed_texts(chunks)

        ids = [
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}:{i}"))
            for i in range(len(chunks))
        ]

        payloads = [
            {"source": source_id, "text": chunks[i]}
            for i in range(len(chunks))
        ]

        QdrantStorage().upsert(ids, vecs, payloads)
        return RAGUpsertResult(ingested=len(chunks))

    chunks_and_src = await ctx.step.run(
        "load-and-chunk",
        lambda: _load(ctx),
        output_type=RAGChunkAndSrc
    )

    ingested = await ctx.step.run(
        "embed-and-upsert",
        lambda: _upsert(chunks_and_src),
        output_type=RAGUpsertResult
    )

    return ingested.model_dump()


# =========================
# 🔍 QUERY FUNCTION (FIXED)
# =========================
@inngest_client.create_function(
    fn_id="RAG: Query PDF",
    trigger=inngest.TriggerEvent(event="rag/query_pdf_ai")
)
async def rag_query_pdf_ai(ctx: inngest.Context):

    def _search(question: str, top_k: int = 5) -> RAGSearchResult:
        query_vec = embed_texts([question])[0]

        store = QdrantStorage()

        dense_results = store.search(query_vec, top_k)

        contexts = dense_results["contexts"]

        return RAGSearchResult(
            contexts=contexts,
            sources=dense_results["sources"]
        )

    question = ctx.event.data["question"]
    top_k = int(ctx.event.data.get("top_k", 5))

    found = await ctx.step.run(
        "embed-and-search",
        lambda: _search(question, top_k),
        output_type=RAGSearchResult
    )

    # 🔹 Build prompt
    context_block = "\n\n".join(f"- {c}" for c in found.contexts)

    user_content = (
        "Use the following context to answer the question.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n"
        "Answer concisely using ONLY the context above."
    )

    # =========================
    # 🔥 DIRECT LLM CALL (NO TIMEOUT)
    # =========================
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You answer questions using only the provided context."},
                {"role": "user", "content": user_content}
            ],
            max_tokens=512,        # 🔥 reduce latency
            temperature=0.2
        )

        answer = response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"LLM Error: {e}")
        answer = "Error generating response. Please try again."

    return {
        "answer": answer,
        "sources": found.sources,
        "num_contexts": len(found.contexts)
    }


# =========================
# 🚀 FASTAPI APP
# =========================

inngest.fast_api.serve(
    app,
    inngest_client,
    [rag_ingest_pdf, rag_query_pdf_ai]
)