"""
test_pipeline.py — Offline pipeline test (no server required).

Run from the backend/ directory:
    venv\\Scripts\\python tests/test_pipeline.py [optional_pdf_path]

Tests:
  1. Imports (config, services)
  2. Embedding generation
  3. PDF extraction + page awareness   (requires a PDF path argument)
  4. Page-aware chunking with metadata
  5. ChromaDB upsert
  6. ChromaDB search (persistence check)
  7. ChromaDB delete
"""

import sys
import os

# Ensure 'backend/' is on the path so 'app.*' imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "[PASS]"
FAIL = "[FAIL]"


def _banner(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


def test_config():
    _banner("1. Config")
    from app.config import (
        UPLOAD_DIR, VECTOR_DB_DIR, CHUNK_SIZE, CHUNK_OVERLAP,
        EMBEDDING_MODEL, EMBEDDING_DIM, MAX_FILE_SIZE_MB,
    )
    assert UPLOAD_DIR.endswith("uploads"), f"Unexpected UPLOAD_DIR: {UPLOAD_DIR}"
    assert VECTOR_DB_DIR.endswith("vector_db"), f"Unexpected VECTOR_DB_DIR: {VECTOR_DB_DIR}"
    print(f"  UPLOAD_DIR   = {UPLOAD_DIR}")
    print(f"  VECTOR_DB_DIR= {VECTOR_DB_DIR}")
    print(f"  CHUNK_SIZE   = {CHUNK_SIZE}")
    print(f"  EMBED_MODEL  = {EMBEDDING_MODEL}  dim={EMBEDDING_DIM}")
    print(f"  MAX_FILE_MB  = {MAX_FILE_SIZE_MB}")
    print(f"{PASS} Config OK")


def test_embedding():
    _banner("2. Embedding")
    from app.services.embedding_service import generate_embedding, EMBEDDING_DIM
    text = "Enterprise document intelligence with semantic search."
    emb = generate_embedding(text)
    assert isinstance(emb, list), "Embedding should be a list"
    assert len(emb) == EMBEDDING_DIM, f"Expected dim={EMBEDDING_DIM}, got {len(emb)}"
    assert all(isinstance(v, float) for v in emb), "All values should be float"
    print(f"  dim={len(emb)}, sample={[round(v,4) for v in emb[:4]]}")
    print(f"{PASS} Embedding OK")
    return emb


def test_pdf_extraction(pdf_path: str):
    _banner("3. PDF Extraction")
    from app.services.pdf_service import extract_pages
    result = extract_pages(pdf_path)

    assert "pages" in result
    assert "page_count" in result
    assert result["page_count"] > 0, "Expected at least 1 page"

    print(f"  page_count   = {result['page_count']}")
    print(f"  total_chars  = {result['total_chars']}")
    print(f"  word_count   = {result['word_count']}")
    print(f"  is_scanned   = {result['is_scanned']}")

    for p in result["pages"][:3]:
        snippet = p["text"][:80].replace("\n", " ")
        print(f"  Page {p['page_number']}: {snippet!r}")

    print(f"{PASS} PDF Extraction OK")
    return result


def test_chunking(pages: list, doc_id: str = "test-doc-001", doc_name: str = "test.pdf"):
    _banner("4. Chunking")
    from app.services.chunk_service import chunk_pages
    chunks = chunk_pages(pages=pages, document_id=doc_id, document_name=doc_name)

    assert len(chunks) > 0, "Expected at least 1 chunk"

    first = chunks[0]
    assert "chunk_id"      in first
    assert "page_number"   in first
    assert "text"          in first
    assert "document_id"   in first
    assert "document_name" in first
    assert "chunk_index"   in first

    print(f"  total_chunks = {len(chunks)}")
    print(f"  first chunk_id = {first['chunk_id']}")
    print(f"  first page_num = {first['page_number']}")
    print(f"  first text len = {len(first['text'])} chars")
    print(f"  pages covered  = {sorted(set(c['page_number'] for c in chunks))}")

    print(f"{PASS} Chunking OK")
    return chunks


def test_chromadb(chunks: list):
    _banner("5–7. ChromaDB (upsert → search → delete)")
    from app.services.embedding_service import generate_embedding
    from app.services.vector_service import (
        upsert_chunks, search_chunks, delete_document_chunks,
        get_document_chunk_count, total_chunk_count,
    )

    # Use first 5 chunks to keep test fast
    test_chunks = chunks[:5]
    doc_id = test_chunks[0]["document_id"]

    # ── Upsert ────────────────────────────────────────────────────────────────
    embeddings = [generate_embedding(c["text"]) for c in test_chunks]
    stored = upsert_chunks(test_chunks, embeddings)
    assert stored == len(test_chunks), f"Expected {len(test_chunks)} stored, got {stored}"
    print(f"  {PASS} Upserted {stored} chunks")

    # ── Count ─────────────────────────────────────────────────────────────────
    count = get_document_chunk_count(doc_id)
    assert count >= len(test_chunks), f"Expected >= {len(test_chunks)} chunks, got {count}"
    print(f"  {PASS} Count check: {count} chunks for doc '{doc_id}'")
    print(f"       Total in DB: {total_chunk_count()}")

    # ── Search (general) ──────────────────────────────────────────────────────
    query_emb = generate_embedding("document intelligence retrieval")
    results = search_chunks(query_emb, k=3)
    assert isinstance(results, list), "search_chunks should return a list"
    print(f"  {PASS} Search (no filter): {len(results)} results")
    if results:
        r = results[0]
        assert "document_name" in r
        assert "page_number"   in r
        assert "score"         in r
        print(f"       Top: doc='{r['document_name']}', page={r['page_number']}, score={r['score']}")

    # ── Search (filtered by doc_id) ───────────────────────────────────────────
    filtered = search_chunks(query_emb, k=3, document_id=doc_id)
    assert all(r["document_id"] == doc_id for r in filtered), "Filter not working"
    print(f"  {PASS} Search (filtered): {len(filtered)} results, all from '{doc_id}'")

    # ── Delete ────────────────────────────────────────────────────────────────
    deleted = delete_document_chunks(doc_id)
    assert deleted == count, f"Expected to delete {count}, deleted {deleted}"
    remaining = get_document_chunk_count(doc_id)
    assert remaining == 0, f"Expected 0 remaining, got {remaining}"
    print(f"  {PASS} Deleted {deleted} chunks, remaining={remaining}")

    print(f"{PASS} ChromaDB OK")


def create_test_pdf(path: str):
    """Create a minimal multi-page PDF for testing."""
    import fitz
    doc = fitz.open()
    for i in range(1, 4):
        page = doc.new_page(width=595, height=842)  # A4
        text = (
            f"Page {i} of the DocIntel test document.\n\n"
            f"This page contains sample enterprise text for testing the "
            f"ingestion pipeline. Paragraph {i}A talks about document "
            f"management and retrieval-augmented generation. "
            f"Paragraph {i}B discusses semantic search and embedding models. "
            f"Paragraph {i}C covers source grounding and citation support."
        )
        page.insert_text((72, 72), text, fontsize=11)
    doc.save(path)
    doc.close()
    print(f"  Created test PDF: {path}")


if __name__ == "__main__":
    print("\nDocIntel AI — Pipeline Test")

    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    errors: list[str] = []

    # Config
    try:
        test_config()
    except Exception as e:
        print(f"{FAIL} Config FAILED: {e}")
        errors.append("config")

    # Embedding
    try:
        test_embedding()
    except Exception as e:
        print(f"{FAIL} Embedding FAILED: {e}")
        errors.append("embedding")

    # PDF — use provided path or auto-create a test one
    if pdf_path is None:
        generated = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_generated.pdf"
        )
        _banner("Creating synthetic test PDF")
        try:
            create_test_pdf(generated)
            pdf_path = generated
        except Exception as e:
            print(f"{FAIL} Could not create test PDF: {e}")
            errors.append("create_pdf")

    if pdf_path and os.path.exists(pdf_path):
        try:
            extraction = test_pdf_extraction(pdf_path)
            chunks = test_chunking(extraction["pages"])
            test_chromadb(chunks)
        except Exception as e:
            import traceback
            print(f"{FAIL} Pipeline FAILED: {e}")
            traceback.print_exc()
            errors.append("pipeline")
    else:
        print(f"{FAIL} No valid PDF path — skipping extraction/chunking/ChromaDB tests")

    # Summary
    print(f"\n{'='*55}")
    if errors:
        print(f"  {FAIL} FAILED: {errors}")
        sys.exit(1)
    else:
        print(f"  {PASS} All tests passed!")
    print(f"{'='*55}\n")
