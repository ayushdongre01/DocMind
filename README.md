# DocMind

DocMind is a PDF question-answering app built with Retrieval-Augmented Generation (RAG). It ingests PDF text, creates local embeddings, stores vectors in Qdrant, and generates grounded answers with source references.

## What Changed In Architecture

The current app flow is API-first:

- Streamlit frontend calls FastAPI endpoints directly.
- FastAPI handles ingestion and querying via `/ingest` and `/query`.
- Qdrant stores and retrieves dense vectors.
- BM25 sparse scoring is used alongside dense retrieval to improve keyword matching during query.
- Inngest functions still exist in backend code for event-driven workflows, but the active UI flow uses direct HTTP endpoints.

## 🌐 Live Demo

👉 Try the app here:  
🔗 [https://doc-mind.streamlit.app/](https://doc-mind.streamlit.app/)

## Architecture

1. User uploads a PDF in Streamlit.
2. Frontend sends file to backend `/ingest`.
3. Backend extracts text with `llama-index` PDF reader.
4. Text is split into chunks (`chunk_size=700`, `chunk_overlap=100`).
5. Chunks are embedded with `all-MiniLM-L6-v2` (384-dim).
6. Vectors and payloads are upserted into Qdrant collection `docs`.
7. User asks a question in Streamlit.
8. Frontend sends question to backend `/query` with `top_k` and document source filter.
9. Backend performs dense retrieval (Qdrant) + sparse retrieval (BM25), merges context, and calls LLM.
10. Backend returns answer, source files, and context count to UI.

## Tech Stack

- Python    
- Streamlit
- FastAPI
- Qdrant
- sentence-transformers (`all-MiniLM-L6-v2`)
- llama-index readers
- rank-bm25
- OpenAI Python SDK (Azure GitHub Models compatible endpoint)
- Inngest (available in backend for event-driven flow)

## Repository Structure

```text
DocMind/
├── main.py                 # FastAPI routes + Inngest functions + LLM calls
├── streamlit_app.py        # Streamlit frontend (upload + QA)
├── data_loader.py          # PDF load/chunk + embedding + BM25 index build
├── vector_db.py            # Qdrant storage wrapper
├── custom_types.py         # Pydantic data models
├── uploads/                # Uploaded PDFs
├── requirements.txt
├── pyproject.toml
└── README.md
```

## API Endpoints

### `POST /ingest`

- Input: multipart file (`pdf`)
- Action: chunk + embed + upsert to Qdrant
- Output: ingested chunk count

### `POST /query`

- Input JSON:

```json
{
	"question": "What is the document about?",
	"top_k": 5,
	"source": "my_file.pdf"
}
```

- Action: retrieve context (dense + sparse), generate LLM answer
- Output: answer text, sources, number of contexts used

## Local Setup

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Run Qdrant locally

```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

## 3. Configure environment

Create `.env` in project root:

```env
OPENAI_API_KEY=your_api_key_here
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
INNGEST_API_BASE=http://127.0.0.1:8288/v1
```

Notes:

- `OPENAI_API_KEY` is required for answer generation.
- `QDRANT_URL` defaults to `http://localhost:6333` if unset.
- `INNGEST_API_BASE` is only needed if using Inngest event flow.

## 4. Run backend

```bash
uvicorn main:app --reload
```

## 5. Run frontend

```bash
streamlit run streamlit_app.py
```

## Configuration Notes

- Embedding model in code: `SentenceTransformer("all-MiniLM-L6-v2")`
- Embedding dimension: `384`
- Qdrant collection: `docs`
- Query default `top_k`: `5`
- LLM model: `gpt-4o-mini`

If you use a local model folder instead of hub download, update model path in `data_loader.py` accordingly.

## Screenshots

![Home Page](https://github.com/ayushdongre01/DocMind/blob/main/images/1.png)
![Question 1](https://github.com/ayushdongre01/DocMind/blob/main/images/2.png)
![Answer 1](https://github.com/ayushdongre01/DocMind/blob/main/images/3.png)
![Question 2](https://github.com/ayushdongre01/DocMind/blob/main/images/4.png)
![Answer 2](https://github.com/ayushdongre01/DocMind/blob/main/images/5.png)

## Troubleshooting

- `401/403` from model endpoint: verify `OPENAI_API_KEY`.
- No search results: confirm Qdrant is running and collection has ingested points.
- Slow responses: reduce `top_k`.
- Wrong source filtering: ensure query `source` matches uploaded filename.
- Embedding load errors: check model availability for `all-MiniLM-L6-v2`.

## Roadmap

- Streaming token responses in UI
- Multi-document session context
- Better ingestion progress tracking
- Per-user document isolation

