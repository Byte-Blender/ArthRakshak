# ArthRakshak

A financial-literacy platform for self-help groups (SHGs): a retrieval-augmented advisor, a WhatsApp assistant, and a trust graph built from group interactions.

**Live demo:** https://arthrakshak-three.vercel.app/

## What's inside

### Lakshmi — RAG financial advisor
- Document ingestion pulls text out of PDFs with `pdfplumber` (`agents/document_ingest.py`)
- 384-dim sentence-transformer embeddings (`agents/embeddings.py`)
- Chunks stored in PostgreSQL with **pgvector**; retrieval returns the top-3 matches
- Answers are generated from the retrieved context through a pluggable LLM client (hosted API or local `llama.cpp`)
- Served by FastAPI (`api/routes.py`)

### Saheli — WhatsApp financial assistant
- Twilio WhatsApp webhook (`api/saheli.py`), handling text and voice input
- Same knowledge base as the advisor, so a user without a smartphone app can still ask questions

### Temporal trust-graph scoring
- NetworkX graph of SHG members over rolling 2-hour windows (`agents/trust_graph.py`)
- Eigenvector centrality to find the connectors who actually carry information through the group

## Architecture

```
frontend/   React 19 + Vite single-page app
backend/
  main.py         FastAPI app, CORS config, /health
  api/routes.py   advisor endpoints
  api/saheli.py   Twilio webhook
  agents/         ingestion, embeddings, retrieval, LLM client, trust graph
  db/             SQLAlchemy models and pgvector setup
```

## Running locally

```bash
# backend
cd backend
pip install -r requirements.txt
# .env: DATABASE_URL=postgresql+psycopg2://..., plus the LLM provider key
uvicorn main:app --reload

# frontend
cd frontend
npm install
npm run dev
```

The front-end dev server runs on `http://localhost:5173`, which is already in the API's CORS allow-list.

## Stack

`Python` · `FastAPI` · `PostgreSQL` · `pgvector` · `SQLAlchemy` · `sentence-transformers` · `NetworkX` · `Twilio` · `React` · `Vite`
<!-- File: README.md | Location: README.md -->
