from dotenv import load_dotenv
import os

load_dotenv()

# --- API Keys ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GEMINI_API_KEY is optional — not currently used (sentence_transformers used for embeddings)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- LLM ---
# Set GROQ_MODEL in .env to override.  Default is the best model confirmed
# available on this Groq account as of 2026-09-04.
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

# --- MongoDB ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# --- Absolute paths (computed from this file's location, always correct) ---
# config.py lives at backend/app/config.py
# BASE_DIR = backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vector_db")

# --- Processing settings ---
MAX_FILE_SIZE_MB = 20
CHUNK_SIZE = 800      # characters per chunk
CHUNK_OVERLAP = 150   # overlap between consecutive chunks
TOP_K_RETRIEVAL = 5   # default top-k for semantic search

# --- Embedding model ---
EMBEDDING_MODEL = "paraphrase-MiniLM-L3-v2"
EMBEDDING_DIM = 384

# --- OCR ---
# Average chars per page below which we flag a PDF as potentially scanned.
# OCR is not currently enabled; this is used for detection and logging only.
OCR_TEXT_THRESHOLD = 50