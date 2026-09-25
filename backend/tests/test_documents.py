"""
test_documents.py — Phase 3: Document management endpoint tests.

Tests GET /documents, GET /documents/{id},
      DELETE /documents/{id}, POST /documents/{id}/reprocess

Requires the server to be running on http://127.0.0.1:8000.
Run this AFTER test_endpoints.py has uploaded at least one document.
"""
from __future__ import annotations

import sys, os, json, urllib.request, urllib.parse, urllib.error, time

BASE = "http://127.0.0.1:8000"
PASS = "[PASS]"
FAIL = "[FAIL]"


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read())

def post(path: str, body: dict | None = None) -> dict:
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def delete(path: str) -> dict:
    req = urllib.request.Request(BASE + path, method="DELETE")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def upload_pdf(pdf_path: str) -> dict:
    boundary = "----DocIntelTestBoundary"
    with open(pdf_path, "rb") as f:
        file_data = f.read()
    filename = os.path.basename(pdf_path)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + "/upload", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def _banner(title: str):
    print(f"\n{'='*58}\n  {title}\n{'='*58}")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_list_documents():
    _banner("GET /documents")
    r = get("/documents")

    assert "total"     in r, "Missing 'total'"
    assert "documents" in r, "Missing 'documents'"
    assert isinstance(r["documents"], list), "'documents' must be a list"

    print(f"  total docs in DB: {r['total']}")
    print(f"  returned:         {len(r['documents'])}")

    if r["documents"]:
        d = r["documents"][0]
        # Verify required fields are present
        for field in ["document_id", "filename", "status", "uploaded_at"]:
            assert field in d, f"Missing field '{field}' in document"
        print(f"  newest doc: [{d['status']}] {d['filename']}")
        print(f"    pages={d.get('page_count',0)}  chunks={d.get('chunk_count',0)}")
        print(f"    uploaded_at={d['uploaded_at']}")
        # uploaded_at must be an ISO string ending in Z
        assert d["uploaded_at"].endswith("Z"), "uploaded_at should be UTC ISO string"

    print(f"{PASS} GET /documents OK")
    return r["documents"][0]["document_id"] if r["documents"] else None


def test_get_document(document_id: str):
    _banner(f"GET /documents/{document_id[:8]}...")
    r = get(f"/documents/{document_id}")

    assert r.get("document_id") == document_id
    assert "status"             in r
    assert "chroma_chunk_count" in r, "Missing live ChromaDB chunk count"
    assert "file_on_disk"       in r, "Missing file_on_disk flag"

    print(f"  document_id:       {r['document_id']}")
    print(f"  filename:          {r['filename']}")
    print(f"  status:            {r['status']}")
    print(f"  page_count:        {r.get('page_count')}")
    print(f"  chunk_count (DB):  {r.get('chunk_count')}")
    print(f"  chroma_chunks:     {r['chroma_chunk_count']}")
    print(f"  file_on_disk:      {r['file_on_disk']}")
    print(f"{PASS} GET /documents/id OK")


def test_404(bad_id: str = "00000000-0000-0000-0000-000000000000"):
    _banner(f"GET /documents/{bad_id} — expect 404")
    try:
        get(f"/documents/{bad_id}")
        print(f"  {FAIL} Should have raised 404")
        return False
    except urllib.error.HTTPError as e:
        assert e.code == 404, f"Expected 404, got {e.code}"
        print(f"  Correctly got HTTP {e.code}")
        print(f"{PASS} 404 for unknown document_id OK")
        return True


def test_reprocess(document_id: str):
    _banner(f"POST /documents/{document_id[:8]}.../reprocess")
    r = post(f"/documents/{document_id}/reprocess")

    assert r.get("document_id") == document_id
    assert r.get("status") == "processed", f"Expected 'processed', got: {r.get('status')}"
    assert "page_count"   in r
    assert "chunk_count"  in r
    assert "old_chunks_removed" in r

    print(f"  status:            {r['status']}")
    print(f"  page_count:        {r['page_count']}")
    print(f"  word_count:        {r['word_count']}")
    print(f"  chunk_count:       {r['chunk_count']}")
    print(f"  old_chunks_removed:{r['old_chunks_removed']}")
    print(f"{PASS} POST /documents/id/reprocess OK")


def test_delete(document_id: str):
    _banner(f"DELETE /documents/{document_id[:8]}...")

    # Verify it exists first
    pre = get(f"/documents/{document_id}")
    assert pre["document_id"] == document_id

    # Delete
    r = delete(f"/documents/{document_id}")
    assert r.get("status") == "deleted", f"Unexpected status: {r}"

    print(f"  status:                 {r['status']}")
    print(f"  filename:               {r['filename']}")
    print(f"  chromadb_chunks_deleted:{r['chromadb_chunks_deleted']}")
    print(f"  file_deleted:           {r['file_deleted']}")
    print(f"  mongo_record_deleted:   {r['mongo_record_deleted']}")

    assert r["mongo_record_deleted"], "MongoDB record not deleted"

    # Verify it's gone — must 404 now
    try:
        get(f"/documents/{document_id}")
        print(f"  {FAIL} Should 404 after delete")
    except urllib.error.HTTPError as e:
        assert e.code == 404, f"Expected 404 after delete, got {e.code}"
        print(f"  Correctly 404 after deletion")

    print(f"{PASS} DELETE /documents/id OK")
    return r


def main():
    # Use the synthetic test PDF; generate if needed
    test_pdf = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test_generated.pdf"
    )
    if not os.path.exists(test_pdf):
        print("test_generated.pdf not found. Run test_pipeline.py first.")
        sys.exit(1)

    print("\nDocIntel AI — Phase 3: Document Management Tests")
    errors: list[str] = []

    # ── Upload a fresh doc to work with ──────────────────────────────────────
    _banner("Setup: uploading fresh test document")
    try:
        up = upload_pdf(test_pdf)
        doc_id = up["document_id"]
        print(f"  Uploaded: {up['filename']}  id={doc_id}  chunks={up['chunk_count']}")
        assert up["status"] == "processed"
        print(f"  {PASS} Upload setup OK")
    except Exception as e:
        print(f"  {FAIL} Upload setup failed: {e}")
        sys.exit(1)

    # ── List ──────────────────────────────────────────────────────────────────
    try:
        test_list_documents()
    except Exception as e:
        print(f"  {FAIL} list_documents: {e}")
        errors.append("list")

    # ── Detail ────────────────────────────────────────────────────────────────
    try:
        test_get_document(doc_id)
    except Exception as e:
        print(f"  {FAIL} get_document: {e}")
        errors.append("detail")

    # ── 404 ───────────────────────────────────────────────────────────────────
    try:
        test_404()
    except Exception as e:
        print(f"  {FAIL} 404 test: {e}")
        errors.append("404")

    # ── Reprocess ─────────────────────────────────────────────────────────────
    try:
        test_reprocess(doc_id)
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  {FAIL} reprocess: {e}")
        errors.append("reprocess")

    # ── Detail after reprocess (verify counts updated) ────────────────────────
    try:
        _banner("GET /documents/id — verify counts after reprocess")
        post_r = get(f"/documents/{doc_id}")
        print(f"  chunk_count after reprocess: {post_r.get('chunk_count')}")
        print(f"  chroma_chunk_count:          {post_r['chroma_chunk_count']}")
        assert post_r["chunk_count"] == post_r["chroma_chunk_count"], (
            f"Mismatch: mongo={post_r['chunk_count']} chroma={post_r['chroma_chunk_count']}"
        )
        print(f"  {PASS} MongoDB + ChromaDB chunk counts in sync after reprocess")
    except Exception as e:
        print(f"  {FAIL} post-reprocess detail: {e}")
        errors.append("post_reprocess_detail")

    # ── Delete ────────────────────────────────────────────────────────────────
    try:
        test_delete(doc_id)
    except Exception as e:
        print(f"  {FAIL} delete: {e}")
        errors.append("delete")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*58}")
    if errors:
        print(f"  {FAIL} FAILED: {errors}")
        sys.exit(1)
    else:
        print(f"  {PASS} ALL Phase-3 document management tests passed!")
    print(f"{'='*58}\n")


if __name__ == "__main__":
    main()
