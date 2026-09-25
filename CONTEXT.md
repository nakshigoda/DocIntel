# Developer Context & System Specification (CONTEXT.md)

This document provides complete developer context, technical implementation specifications, design decisions, and system architecture details for **DocIntel AI**.

---

## 1. Project Purpose

DocIntel AI is a Retrieval-Augmented Generation (RAG) and Enterprise Document Intelligence platform. It solves the challenge of extracting, indexing, searching, summarizing, comparing, and querying large enterprise PDF collections with complete factual accuracy, zero hallucination, and explicit source citations (document name + 1-indexed page number).

---

## 2. Current Implementation Status

The project is fully implemented, integrated, and verified end-to-end. All core phases are complete:
- ✅ **Backend Processing**: FastAPI server running on Python 3.13.
- ✅ **Document Ingestion**: Page-aware PDF parsing, text cleaning, scanned PDF detection.
- ✅ **Chunking Engine**: Page-boundary-preserving character chunking with configurable size & overlap.
- ✅ **Dense Embeddings**: Local 384-dimensional embeddings via `SentenceTransformer("paraphrase-MiniLM-L3-v2")`.
- ✅ **Persistent Vector Store**: ChromaDB persistent vector database with cosine similarity metric.
- ✅ **Metadata Storage**: MongoDB database tracking document status (`uploaded`, `processing`, `processed`, `failed`), page counts, word counts, and timestamps.
- ✅ **Grounded RAG Q&A**: LLM generation via Groq Cloud API (`qwen/qwen3.8-27b`) with automatic `<think>` tag stripping.
- ✅ **Document Intelligence**: Executive summarization, structured JSON entity extraction, and side-by-side document comparison.
- ✅ **Frontend Dashboard**: Responsive Next.js 16 (Turbopack) dashboard with TypeScript and Tailwind CSS.
- ✅ **Testing & Verification**: 5 automated test scripts covering pipeline unit tests, REST endpoints, restart persistence, document management CRUD, and intelligence capabilities.

---

## 3. High-Level Architecture & Component Stack

```
[User Browser]
      │
      ▼
[Next.js 16 Dashboard] (React 19, TypeScript, Tailwind CSS, Lucide React)
      │
      ▼ (HTTP REST APIs)
[FastAPI Server] (app/main.py)
      │
      ├─► [PDF Service] (PyMuPDF / fitz - page-by-page text cleaning)
      ├─► [Chunk Service] (Page-aware overlapping chunker)
      ├─► [Embedding Service] (SentenceTransformers - paraphrase-MiniLM-L3-v2, 384-dim)
      ├─► [Vector Service] (ChromaDB - PersistentClient, document_chunks collection, cosine space)
      ├─► [Database Service] (MongoDB - docintel.documents collection)
      ├─► [LLM Service] (Groq API - qwen/qwen3.8-27b, grounding prompt & <think> stripper)
      ├─► [Summarization Service] (Executive summaries, key points, risks, action items)
      ├─► [Extraction Service] (Structured JSON attribute extraction)
      └─► [Comparison Service] (Side-by-side document diff analysis)
```

---

## 4. Backend Architecture

- **Framework**: FastAPI (version `0.136.3`) served via Uvicorn (`0.49.0`).
- **Structure**: Clean separation of concerns between `app/main.py` (entry point), `app/config.py` (configuration & absolute path computations), `app/routes/` (REST endpoint controllers), and `app/services/` (business logic engines).
- **CORS Middleware**: Registered globally in `app/main.py` before routes to allow frontend integration (`http://localhost:3000`).
- **Error Handling**: Graceful exception handling in ingestion pipelines, updating MongoDB document status to `failed` and capturing error messages without crashing the server.

---

## 5. Frontend Architecture

- **Framework**: Next.js `16.2.9` (App Router with Turbopack) + React `19.2.4`.
- **Styling**: Tailwind CSS v3 + Lucide React icon suite.
- **State Management**: React state hooks (`useState`, `useEffect`, `useCallback`) managing tab switching, document selection, upload modal, search query states, and chat message history.
- **API Integration Layer**: `frontend/lib/api.ts` provides strongly-typed asynchronous client methods wrapping all FastAPI endpoints.

---

## 6. Document Ingestion Flow

1. **Upload Request**: Client sends a PDF via `POST /upload`.
2. **Validation**:
   - Filename extension check (`.pdf`).
   - Magic bytes check (`b"%PDF"`).
   - Size check (capped at `MAX_FILE_SIZE_MB = 20`).
3. **Storage & Mongo Entry**:
   - File saved to `backend/uploads/{uuid}_{safe_filename}`.
   - Initial MongoDB document created (`status: uploaded`).
4. **Text Extraction**: `pdf_service.extract_pages()` extracts page-by-page text using PyMuPDF.
5. **Text Cleaning**: `pdf_service._clean_text()` rejoins hyphenated line breaks (`infor-\nmation` → `information`), normalizes paragraph breaks, and removes control characters.
6. **Scanned PDF Check**: Calculates average character count per page. If average < `OCR_TEXT_THRESHOLD` (50 chars), sets `is_scanned: true` and logs warning.
7. **Chunking**: `chunk_service.chunk_pages()` creates page-aware overlapping chunks tagged with unique `chunk_id` (`{doc_id}_p{page}_c{index}`).
8. **Embedding & Vector Storage**: Chunks are embedded via `embedding_service.generate_embedding()` and upserted into ChromaDB via `vector_service.upsert_chunks()`.
9. **Final MongoDB Update**: MongoDB document updated to `status: processed` with page count, word count, character count, and chunk count.

---

## 7. Embedding Model & Vector Store Specifications

### Embedding Model
- **Library**: `sentence-transformers==5.5.1`
- **Model**: `paraphrase-MiniLM-L3-v2`
- **Dimensionality**: 384 dimensions
- **Execution Mode**: Local CPU thread-safe singleton (`_get_model()`). Zero API costs, zero external network dependency.

### Vector Database
- **Engine**: ChromaDB `1.5.9` (`chromadb.PersistentClient`)
- **Directory**: `backend/vector_db/`
- **Collection**: `document_chunks`
- **Metric**: Cosine similarity (`metadata={"hnsw:space": "cosine"}`)
- **Metadata Fields**: `document_id`, `document_name`, `page_number`, `chunk_index`
- **Score Calculation**: Distance converted to similarity score: `score = round(max(0.0, 1.0 - distance), 4)`

---

## 8. RAG Retrieval & Prompt Grounding Strategy

### Retrieval Engine (`vector_service.search_chunks`)
- Query text embedded using local `generate_embedding()`.
- Nearest-neighbor query executed against ChromaDB collection.
- Optional metadata filtering: `where={"document_id": {"$eq": doc_id}}` when scope is restricted to a single document.
- Returns top-*k* chunks (default *k*=5).

### Prompt Construction & LLM Execution (`llm_service.generate_answer`)
- Context assembled with source headers:
  ```
  [Source: Document_Name.pdf, Page 12]
  Chunk text content...
  
  ---
  
  [Source: Document_Name.pdf, Page 14]
  Chunk text content...
  ```
- **System Instructions**:
  - Answer ONLY using the provided context.
  - If answer is not present, respond: *"This information was not found in the provided documents."*
  - Cite source document name and page number for every claim.
  - Do NOT invent facts outside the text.
- **LLM Call**: Groq API (`qwen/qwen3.8-27b`), `temperature=0.1`, `max_tokens=1024`.
- **Thinking Token Stripper**: `_strip_thinking()` uses regular expressions and fallbacks to strip reasoning blocks (`<think>...</think>`) before returning the final response.

---

## 9. MongoDB Database Schema

- **Database**: `docintel`
- **Collection**: `documents`
- **Fields**:
  - `document_id` (str): UUID string key.
  - `filename` (str): Original user filename.
  - `stored_filename` (str): Disk filename on backend.
  - `filepath` (str): Absolute file path.
  - `file_size_bytes` (int): File size.
  - `uploaded_at` (datetime): Upload timestamp.
  - `status` (str): `"uploaded"` | `"processing"` | `"processed"` | `"failed"`.
  - `page_count` (int): Total PDF pages.
  - `word_count` (int): Total word count.
  - `character_count` (int): Total character count.
  - `chunk_count` (int): Number of indexed chunks in ChromaDB.
  - `is_scanned` (bool): Scanned PDF flag.
  - `processed_at` (datetime): Completion timestamp.
  - `error` (str | null): Error details if status is `"failed"`.

---

## 10. Summary of API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Root API metadata & system version |
| `GET` | `/health` | Health check endpoint |
| `POST` | `/upload` | Upload & ingest PDF document |
| `GET` | `/documents` | List uploaded documents (newest first, paginated) |
| `GET` | `/documents/{id}` | Get document metadata & live ChromaDB count |
| `DELETE` | `/documents/{id}` | Complete atomic deletion (MongoDB + ChromaDB + disk) |
| `POST` | `/documents/{id}/reprocess` | Re-run ingestion pipeline on existing file |
| `GET` | `/search` | Semantic vector search across document collection |
| `GET` | `/chat` | Grounded RAG Q&A with source citations |
| `POST` | `/summarize/{id}` | Generate executive summary, key points, risks |
| `POST` | `/extract/{id}` | Extract structured JSON fields & entities |
| `POST` | `/compare` | Compare two document versions side-by-side |

---

## 11. Environment Configuration

Defined in `backend/.env` (and standard `.env.example` template):

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
MONGO_URI=mongodb://localhost:27017
```

---

## 12. Design Decisions & Rationale

1. **SentenceTransformers Local Embeddings vs Cloud APIs**:
   - Using `paraphrase-MiniLM-L3-v2` locally avoids API rate limits, costs, and dependencies on external embedding models. It produces 384-dimensional vectors fast on standard laptop CPUs.
2. **ChromaDB over FAISS for Production Persistence**:
   - ChromaDB provides native metadata filtering (`document_id`), chunk deletion by ID, and JSON metadata storage in a clean persistent directory structure.
3. **Reasoning Tag Stripping (`<think>`)**:
   - Modern reasoning models like `qwen/qwen3.8-27b` produce internal thought tokens inside `<think>` tags. The backend cleans these before returning output, providing a clean response for the UI.
4. **Stateless Q&A Design**:
   - Each RAG query explicitly embeds the question and retrieves top chunks, preventing hallucination accumulation across multi-turn sessions.

---

## 13. System Limitations & Known Boundaries

- **Scanned PDF Support**: Text extraction relies on PyMuPDF text layers. Scanned or image-only PDFs are flagged automatically (`is_scanned: true`); dedicated OCR (e.g. Tesseract) can be attached to `pdf_service.py`.
- **File Format Focus**: Optimized specifically for PDF documents (`.pdf`).
- **Stateless Chat Context**: Queries are stateless; multi-turn conversation memory is not saved across sessions.

---

## 14. How to Run the Project

### Start Backend
```bash
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Run Tests
```bash
cd backend
python tests/test_pipeline.py
python tests/test_endpoints.py
python tests/test_persistence.py
python tests/test_documents.py
python tests/test_intelligence.py
```
