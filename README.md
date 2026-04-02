# DocMind

DocMind is a local retrieval-augmented generation (RAG) app for asking questions about PDF documents. You upload a document in the Streamlit UI, the app chunks and embeds the text, stores vectors in Qdrant, and then uses an LLM to answer questions with supporting context.

## What It Does

- Upload PDF files and persist them in a local `uploads/` folder.
- Extract text from PDFs with `llama-index` readers.
- Split documents into overlapping text chunks for retrieval.
- Generate embeddings with a local SentenceTransformer model.
- Store and search chunks in Qdrant.
- Send questions through an Inngest-based workflow and generate answers with the OpenAI-compatible client configured for Azure GitHub Models.
- Show sources for retrieved context in the UI.

## Architecture

1. The Streamlit app accepts a PDF upload.
2. The PDF is saved locally under `uploads/`.
3. An Inngest event named `rag/ingest_pdf` triggers ingestion.
4. The backend loads the PDF, splits it into chunks, embeds the chunks, and upserts them into Qdrant.
5. When you ask a question, the Streamlit app sends a `rag/query_pdf_ai` event.
6. The backend embeds the question, searches Qdrant for the top matches, and sends the retrieved context to the LLM.
7. The answer and source references are returned to the UI.

## Tech Stack

- Python 3.13+
- FastAPI
- Streamlit
- Inngest
- Qdrant
- sentence-transformers
- llama-index
- OpenAI-compatible client configured for Azure GitHub Models

## Repository Layout

```text
DocMind/
├── main.py                # FastAPI app and Inngest functions
├── streamlit_app.py       # Document upload and chat UI
├── data_loader.py         # PDF loading, chunking, and embedding helpers
├── vector_db.py           # Qdrant wrapper for insert/search
├── custom_types.py        # Pydantic response models
├── models/
│   └── all-MiniLM-L6-v2/  # Local embedding model files
├── uploads/               # Uploaded PDFs are saved here
├── qdrant_storage/        # Local Qdrant data directory
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.13 or newer
- Qdrant running locally on port `6333`
- Access to an OpenAI-compatible model endpoint through `OPENAI_API_KEY`
- The local embedding model available at `models/all-MiniLM-L6-v2`

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

If you prefer to use the project metadata, you can also install from `pyproject.toml` with your preferred Python environment manager.

### 2. Start Qdrant

If Qdrant is not already running, start it locally:

```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

### 3. Configure environment variables

Create a `.env` file in the project root with the values your setup needs:

```env
OPENAI_API_KEY=your_api_key_here
INNGEST_API_BASE=http://127.0.0.1:8288/v1
```

Notes:

- `OPENAI_API_KEY` is used by the OpenAI-compatible client in `main.py`.
- `INNGEST_API_BASE` is optional, but it must point to the Inngest API server if you are not using the default local address.

### 4. Verify the local embedding model

The app loads the embedding model from `models/all-MiniLM-L6-v2`. If you move the project or change the folder name, update the model path in `data_loader.py` so it points to the correct location.

## Running the App

Open two terminals.

### Backend

Run the FastAPI app that serves the Inngest functions:

```bash
uvicorn main:app --reload
```

### Frontend

Run the Streamlit UI:

```bash
streamlit run streamlit_app.py
```

## How To Use

1. Open the Streamlit app in your browser.
2. Upload a PDF document.
3. Wait for ingestion to complete.
4. Ask a question about the document.
5. Review the generated answer and expand the sources list if references are available.

## Event Flow

The current implementation uses Inngest events rather than direct upload/chat HTTP endpoints.

- `rag/ingest_pdf` handles PDF ingestion.
- `rag/query_pdf_ai` handles question answering.

The UI sends events to Inngest, and the backend functions perform the work and return the final result.

## Configuration Details

### Embeddings

- Chunk size: `700`
- Chunk overlap: `100`
- Embedding dimension: `384`
- Embedding model: `all-MiniLM-L6-v2`

### Retrieval

- Qdrant collection: `docs`
- Distance metric: cosine similarity
- Default `top_k`: `5`

### LLM

- The response generation step uses an OpenAI-compatible client.
- The code currently targets `gpt-4o-mini` through the Azure GitHub Models base URL configured in `main.py`.

## Screenshots

![Home Page](https://github.com/ayushdongre01/DocMind/blob/main/images/1.png)
![Question 1](https://github.com/ayushdongre01/DocMind/blob/main/images/2.png)
![Answer 1](https://github.com/ayushdongre01/DocMind/blob/main/images/3.png)
![Question 2](https://github.com/ayushdongre01/DocMind/blob/main/images/1.png)
![Answer 2](https://github.com/ayushdongre01/DocMind/blob/main/images/2.png)

## Troubleshooting

- If uploads fail, confirm Qdrant is running on `http://localhost:6333`.
- If embeddings fail to load, verify that the local model folder exists and the path in `data_loader.py` is correct.
- If the UI cannot fetch run results, check the `INNGEST_API_BASE` value.
- If responses fail, confirm that `OPENAI_API_KEY` is set and valid for the configured endpoint.
- If PDFs are not returning useful answers, try increasing `top_k` or asking more specific questions.

## Future Improvements

- Streaming responses
- Chat history persistence
- Multiple document collections
- Authentication
- Better upload progress feedback

