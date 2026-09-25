# DocIntel

## Overview

**DocIntel** is an Enterprise Document Intelligence and Retrieval-Augmented Generation (RAG) platform. It provides an end-to-end system for uploading, parsing, chunking, indexing, searching, summarizing, comparing, and querying complex enterprise PDF documents with grounded source citations and zero hallucination.

The platform combines a **FastAPI** backend, **PyMuPDF** text processing, **Sentence Transformers** local embedding generation, **ChromaDB** persistent vector storage, **MongoDB** document metadata tracking, **Groq Cloud API** (`qwen/qwen3.8-27b`) LLM inference, and a **Next.js 16** enterprise dashboard.

---

## Problem Statement

Enterprise organizations deal with hundreds of unstructured PDF documents—such as contracts, policies, financial statements, and technical specifications. Manually reading, searching, summarizing, and comparing these documents is time-consuming and error-prone. Traditional keyword search fails to capture semantic meaning, while standard generative LLM chatbots often hallucinate facts when asked about proprietary documents.

---

## Objectives

- **Eliminate Hallucinations**: Enforce strict context grounding so the LLM answers *only* using information extracted from verified document chunks.
- **Provide Source Provenance**: Attribute every answer to exact source documents and 1-indexed page numbers.
- **Perform Semantic Search**: Enable natural language search across document repositories using high-precision cosine vector similarity.
- **Automate Document Intelligence**: Provide automated executive summarization, structured field extraction (parties, dates, terms, clauses), and side-by-side document comparison.
- **Maintain Low System Overhead**: Run local embeddings on CPU without external embedding API costs or memory-heavy local LLM setups.

---

## Key Features

- **Document Repository Management**: Upload PDFs, inspect chunk metadata, monitor processing status (`uploaded` → `processing` → `processed` / `failed`), reprocess, or delete documents.
- **Page-Aware PDF Parsing & Cleaning**: Preserves 1-indexed page boundaries, rejoins hyphenated line wraps, cleans control characters, and flags scanned/image-only PDFs.
- **Local Dense Embeddings**: Generates 384-dimensional dense vectors locally using `SentenceTransformer("paraphrase-MiniLM-L3-v2")`.
- **Persistent Vector Store**: Persists chunks and embeddings in ChromaDB with cosine similarity distance metrics and metadata filtering.
- **Grounded RAG Q&A**: Answers natural language questions scoped across all documents or filtered to a single document.
- **Source Citations**: Returns document name, page number, relevance score, and snippet for every referenced chunk.
- **Automatic Reasoning Tag Stripping**: Cleans internal model reasoning blocks (`<think>...</think>`) before returning answers to the user.
- **Semantic Vector Search**: Searches document collections with relevance percentage scoring and highlighted text snippets.
- **Executive Summarization**: Generates executive summaries, key points, important clauses, risks, and action items.
- **Structured Field Extraction**: Extracts structured attributes (document type, subject, parties, dates, financial terms, obligations, clauses) into JSON.
- **Document Comparison**: Compares two document versions to highlight additions, omissions, modified terms, and risk impact.
- **Modern Enterprise Dashboard**: Responsive Next.js 16 dashboard with Sidebar navigation, stats cards, document table, chat panel, search panel, compare view, and insights viewer.

---

## RAG Architecture

```
                               ┌─────────────────────────────────────────┐
                               │             USER / BROWSER              │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │     Next.js 16 Enterprise Dashboard     │
                               └────────────────────┬────────────────────┘
                                                    │ REST API
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │           FastAPI REST Server           │
                               └──────┬───────────────────────────┬──────┘
                                      │                           │
                                      ▼                           ▼
                     ┌──────────────────────────┐    ┌──────────────────────────┐
                     │ Document Ingestion Engine│    │  Semantic RAG / LLM      │
                     └────────────┬─────────────┘    └────────────┬─────────────┘
                                  │                               │
       ┌──────────────────────────┼────────────────────────┐      │
       ▼                          ▼                        ▼      │
┌──────────────┐         ┌─────────────────┐       ┌────────────┐ │
│   PyMuPDF    │         │SentenceTransform│       │  MongoDB   │ │
│Page Extraction         │ 384-dim Embeds  │       │Metadata    │ │
└──────┬───────┘         └────────┬────────┘       └────────────┘ │
       │                          │                               │
       ▼                          ▼                               │
┌──────────────┐         ┌─────────────────┐                      │
│ Page-Aware   │         │    ChromaDB     │◄─────────────────────┼── Vector Search
│ Chunking     ├────────►│ Vector Database │                      │   (Top-k Hits)
└──────────────┘         └─────────────────┘                      │
                                                                  ▼
                                                   ┌────────────────────────────┐
                                                   │    Groq Cloud API          │
                                                   │  (qwen/qwen3.8-27b)        │
                                                   └──────────────┬─────────────┘
                                                                  │
                                                                  ▼
                                                   ┌────────────────────────────┐
                                                   │ Grounded Answer +          │
                                                   │ Source Citations           │
                                                   └────────────────────────────┘
```

---

## How It Works

1. **Document Upload**: PDF file is validated (extension check, magic bytes check `%PDF`, 20 MB size limit), stored locally with a UUID prefix, and an initial record (`status: uploaded`) is written to MongoDB.
2. **Text Extraction**: PyMuPDF extracts text page-by-page. Text is cleaned by rejoining hyphenated line wraps (`infor-\nmation` → `information`), normalizing spaces, and stripping invalid bytes. Average character count per page is checked to detect scanned PDFs.
3. **Page-Aware Chunking**: Text is split into overlapping chunks (default 800 characters, 150 character overlap). Each chunk is assigned a globally unique ID (`{doc_id}_p{page}_c{index}`) preserving exact page provenance.
4. **Embedding Generation**: Local `SentenceTransformer("paraphrase-MiniLM-L3-v2")` converts each chunk into a 384-dimensional dense vector embedding.
5. **Vector Storage**: Chunks, embeddings, and metadata (`document_id`, `document_name`, `page_number`, `chunk_index`) are upserted into a persistent ChromaDB collection (`document_chunks`) using cosine similarity metrics. MongoDB status updates to `processed`.
6. **Semantic Retrieval**: Given a user query, the query string is embedded locally and nearest-neighbor search is executed against ChromaDB (with optional `document_id` filtering). Top-*k* relevant chunks are returned with similarity scores.
7. **Context Assembly**: Retrieved chunks are assembled into a structured prompt containing system instructions, source headers (`[Source: Document.pdf, Page X]`), and the user question.
8. **LLM Response Generation**: The Groq API (`qwen/qwen3.8-27b`) generates a grounded response. Internal `<think>...</think>` reasoning tokens are stripped, and the response is returned alongside source citations.

---

## Supported Documents

- **Formats**: PDF (`.pdf`)
- **Types**: Text-based PDFs (scanned/image-only PDFs are detected and flagged with warnings for OCR extensibility).
- **Size Limit**: Up to 20 MB per file.

---

## Embedding Model

- **Model**: `paraphrase-MiniLM-L3-v2` (`sentence-transformers`)
- **Dimensionality**: 384 dimensions
- **Execution**: Local CPU inference (no API key required, zero rate limits, low latency).
- **Rationale**: Provides high-quality semantic sentence representations while keeping memory footprint extremely small (~150 MB RAM).

---

## Vector Database

- **Database**: **ChromaDB** (`chromadb.PersistentClient`)
- **Storage Location**: `backend/vector_db/`
- **Collection**: `document_chunks`
- **Metric**: Cosine similarity (`metadata={"hnsw:space": "cosine"}`)
- **Features**: Persistent storage across server restarts, metadata filtering by `document_id`, and batch deletion by document ID.

---

## LLM Integration

- **Provider**: **Groq Cloud API** (`groq` Python SDK)
- **Model**: `qwen/qwen3.8-27b` (configurable via `GROQ_MODEL` environment variable)
- **Roles**:
  - **RAG Q&A**: Answers questions strictly grounded in retrieved document chunks.
  - **Executive Summarization**: Generates structured summaries (Executive Summary, Key Points, Clauses, Risks, Action Items).
  - **Structured Field Extraction**: Extracts key attributes into JSON.
  - **Document Comparison**: Analyzes differences between two document versions.
- **Reasoning Tag Stripping**: Includes `_strip_thinking()` helper to remove model chain-of-thought blocks (`<think>...</think>`) before delivering answers to the client.

---

## Storage & Database

- **Database**: **MongoDB** (`pymongo`)
- **Connection URI**: `mongodb://localhost:27017`
- **Database Name**: `docintel`
- **Collection**: `documents`
- **Stored Data**: Document ID, original filename, stored filename, file path, size, upload timestamp, page count, word count, character count, chunk count, scanned flag, processing status (`uploaded` | `processing` | `processed` | `failed`), and processing error messages.

---

## API Endpoints

### Health & System
- `GET /` — Root status and API metadata.
- `GET /health` — Liveness health check endpoint.

### Document Management
- `POST /upload` — Upload and process a PDF document.
- `GET /documents` — List all uploaded documents with pagination.
- `GET /documents/{document_id}` — Get single document details & live ChromaDB chunk count.
- `DELETE /documents/{document_id}` — Delete a document completely from MongoDB, ChromaDB, and disk.
- `POST /documents/{document_id}/reprocess` — Re-run the ingestion pipeline on an existing document.

### Search & Q&A
- `GET /search?query={q}&document_id={id}` — Semantic vector search returning top chunks with similarity scores.
- `GET /chat?query={q}&document_id={id}` — Grounded RAG Q&A returning an answer with source citations.

### Document Intelligence
- `POST /summarize/{document_id}` — Generate executive summary, key points, clauses, risks, and action items.
- `POST /extract/{document_id}` — Extract structured JSON fields.
- `POST /compare` — Compare two documents (`document_id_a` and `document_id_b`).

---

## Tech Stack

| Component | Technology |
|---|---|
| **Backend Framework** | Python 3.13 + FastAPI + Uvicorn |
| **Document Parsing** | PyMuPDF (`fitz`) |
| **Embeddings** | SentenceTransformers (`paraphrase-MiniLM-L3-v2`, 384-dim) |
| **Vector Database** | ChromaDB 1.5.9 |
| **Metadata Database** | MongoDB 4.17 (`pymongo`) |
| **LLM Provider** | Groq Cloud API (`groq` SDK) |
| **LLM Model** | `qwen/qwen3.8-27b` (configurable) |
| **Frontend Framework** | Next.js 16 (Turbopack) + React 19 + TypeScript |
| **Styling & UI** | Tailwind CSS + Lucide React |

---

## Project Structure

```
docintel/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application & router setup
│   │   ├── config.py                # Configuration & environment variables
│   │   ├── routes/
│   │   │   ├── upload.py            # POST /upload endpoint
│   │   │   ├── documents.py         # GET/DELETE /documents management endpoints
│   │   │   ├── search.py            # GET /search endpoint
│   │   │   ├── chat.py              # GET /chat RAG endpoint
│   │   │   ├── summarize.py         # POST /summarize & /extract endpoints
│   │   │   └── compare.py           # POST /compare endpoint
│   │   └── services/
│   │       ├── database.py          # MongoDB connection
│   │       ├── pdf_service.py       # PyMuPDF text extraction & cleaning
│   │       ├── chunk_service.py     # Page-aware chunking
│   │       ├── embedding_service.py # Local SentenceTransformers embedding generator
│   │       ├── vector_service.py    # ChromaDB persistent client & vector search
│   │       ├── llm_service.py       # Groq API client & grounding prompt logic
│   │       ├── summarization_service.py # Summarization engine
│   │       ├── extraction_service.py    # JSON extraction engine
│   │       └── comparison_service.py    # Document diff analyzer
│   ├── tests/                       # Test scripts
│   ├── .env.example                 # Environment variable template
│   └── requirements.txt             # Python dependencies
│
└── frontend/
    ├── app/
    │   ├── page.tsx                 # Main Enterprise Dashboard shell
    │   └── layout.tsx
    ├── components/
    │   ├── Sidebar.tsx              # Dashboard sidebar navigation
    │   ├── DashboardView.tsx        # Overview analytics cards & recent uploads
    │   ├── DocumentsView.tsx        # Repository management table & detail modal
    │   ├── ChatView.tsx             # RAG Q&A interface with source citations
    │   ├── SearchView.tsx           # Vector search interface
    │   ├── CompareView.tsx          # Document comparison interface
    │   ├── InsightsView.tsx         # Summarization & structured extraction view
    │   └── UploadModal.tsx          # Drag-and-drop file uploader
    └── lib/
        └── api.ts                   # Typed API client for FastAPI backend
```

---

## Installation

### Prerequisites
- Python 3.13+
- Node.js v22+
- MongoDB Server running locally on `mongodb://localhost:27017`
- Groq API Key (Free from [Groq Console](https://console.groq.com/))

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install
```

---

## Configuration

Create a `.env` file in the `backend/` directory using `.env.example` as a template:

```env
# Groq API Key (Required)
GROQ_API_KEY=gsk_your_groq_api_key_here

# LLM Model (Default: qwen/qwen3.8-27b)
GROQ_MODEL=qwen/qwen3.8-27b

# MongoDB URI (Default: mongodb://localhost:27017)
MONGO_URI=mongodb://localhost:27017
```

*Note: Never commit `.env` containing real credentials to source control.*

---

## Running the Application

### 1. Start FastAPI Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

FastAPI server runs on `http://127.0.0.1:8000`. Swagger docs available at `http://127.0.0.1:8000/docs`.

### 2. Start Next.js Frontend

```bash
cd frontend
npm run dev
```

Dashboard runs on `http://localhost:3000`.

### 3. Run Test Suite

```bash
cd backend
python tests/test_pipeline.py     # Test offline extraction & ChromaDB pipeline
python tests/test_endpoints.py    # Test live REST API endpoints
python tests/test_persistence.py  # Test ChromaDB persistence after restart
python tests/test_documents.py    # Test document management CRUD
python tests/test_intelligence.py # Test summarization, extraction, and comparison
```

---

## Example Workflow

1. **Upload Document**: Drag & drop `Employee_Handbook.pdf` in the dashboard or send `POST /upload`. The file is extracted, chunked, embedded, and stored in ChromaDB and MongoDB.
2. **Semantic Search**: Search for *"annual leave entitlement"* on the Search tab or `GET /search?query=annual+leave`. Returns top vector matches with similarity scores (e.g., `85.4%`) and page numbers (e.g., `Page 12`).
3. **Ask AI (RAG Q&A)**: Ask *"How many vacation days do employees get?"*. The system retrieves relevant chunks from `Employee_Handbook.pdf`, sends them to Groq (`qwen/qwen3.8-27b`), and returns a grounded answer with citations:
   > *"Employees are entitled to 20 days of paid annual leave per calendar year. [Source: Employee_Handbook.pdf, Page 12]"*
4. **Summarize & Extract**: Click **Insights** to view a structured executive summary or extract key dates, parties, and obligations into structured JSON.
5. **Compare**: Select `Policy_v1.pdf` and `Policy_v2.pdf` on the **Compare** tab to view additions, removals, and risk impacts.

---

## Limitations

- **Image-Only Scanned PDFs**: Text extraction relies on PyMuPDF. Scanned PDFs without OCR text layers are flagged automatically (`is_scanned: true`); dedicated OCR integration can be attached via modular extension.
- **Stateless Chat**: Queries do not persist multi-turn conversational history; each RAG query independently retrieves context for the current question.
- **Single File Format**: Currently focused specifically on PDF files (`.pdf`).

---

## Future Improvements

- **OCR Engine Integration**: Add Tesseract or cloud OCR fallbacks for scanned PDFs.
- **Multi-Format Support**: Support DOCX, TXT, and Markdown files.
- **Multi-Turn Chat Sessions**: Persist conversation threads with user session management.
- **Advanced Reranking**: Integrate Cohere or BGE rerankers for enhanced top-*k* chunk precision.

---

## Author

**Nakshi Goda**  
DocIntel AI Project
