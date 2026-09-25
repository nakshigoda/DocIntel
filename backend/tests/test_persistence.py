"""
test_persistence.py — Verifies ChromaDB survives a server restart.

Run AFTER restarting the server WITHOUT re-uploading any documents.
If this passes, data truly persists between application restarts.
"""
from __future__ import annotations
import sys, os, json, urllib.request, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = "http://127.0.0.1:8000"
PASS = "[PASS]"
FAIL = "[FAIL]"


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read())


def main():
    print("\n=== PERSISTENCE TEST (no upload — fresh server restart) ===\n")
    errors = []

    # ── 1. ChromaDB in-process count ─────────────────────────────────────────
    print("1. Checking ChromaDB chunk count via vector_service...")
    try:
        from app.services.vector_service import total_chunk_count
        count = total_chunk_count()
        print(f"   ChromaDB chunks persisted: {count}")
        assert count > 0, "ChromaDB is empty after restart — data was lost!"
        print(f"   {PASS} ChromaDB data persisted across restart")
    except Exception as e:
        print(f"   {FAIL} ChromaDB check failed: {e}")
        errors.append("chromadb_persist")

    # ── 2. /search on persisted data ─────────────────────────────────────────
    print("\n2. GET /search on persisted data (no new upload)...")
    try:
        r = get("/search?query=" + urllib.parse.quote("enterprise document intelligence"))
        print(f"   total results: {r['total']}")
        for hit in r["results"][:3]:
            print(
                f"   -> [{hit['document_name']}] p.{hit['page_number']} "
                f"score={hit['score']}  '{hit['snippet'][:50]}...'"
            )
        assert r["total"] > 0, "Search returned 0 results on persisted data"
        print(f"   {PASS} Search works on persisted data")
    except Exception as e:
        print(f"   {FAIL} Search failed: {e}")
        errors.append("search_persist")

    # ── 3. /chat with source citations ───────────────────────────────────────
    print("\n3. GET /chat — RAG with source citations on persisted data...")
    try:
        r = get("/chat?query=" + urllib.parse.quote("What topics does this document cover?"))
        answer = r.get("answer", "")
        sources = r.get("sources", [])
        print(f"   answer ({len(answer)} chars): {answer[:250]}")
        print(f"   sources returned: {len(sources)}")
        for s in sources:
            print(
                f"   -> [{s['document_name']}] p.{s['page_number']} "
                f"score={s['score']}  snippet='{s['snippet'][:60]}...'"
            )

        assert "answer" in r,         "No 'answer' key in chat response"
        assert len(answer) > 0,        "Answer is empty"
        assert len(sources) > 0,       "No source citations returned"
        # Confirm <think> was stripped — answer should not contain <think>
        assert "<think>" not in answer, "Raw <think> content leaked into answer!"
        print(f"   {PASS} RAG answer is clean (no <think> content)")
        print(f"   {PASS} Source citations present with document name + page number")
    except Exception as e:
        import traceback
        print(f"   {FAIL} Chat failed: {e}")
        traceback.print_exc()
        errors.append("chat_persist")

    # ── 4. Document-specific filter ───────────────────────────────────────────
    print("\n4. Testing document-specific RAG filter...")
    try:
        # Get a doc_id from search results
        r_search = get("/search?query=" + urllib.parse.quote("pipeline"))
        if r_search["total"] > 0:
            doc_id = r_search["results"][0]["document_id"]
            r_chat = get(
                "/chat?query=" + urllib.parse.quote("What is this document about?")
                + "&document_id=" + doc_id
            )
            # All sources must be from the filtered doc
            for s in r_chat.get("sources", []):
                assert s["document_id"] == doc_id, (
                    f"Filter broken: got doc_id={s['document_id']}, "
                    f"expected {doc_id}"
                )
            print(f"   Filtered to doc_id={doc_id}")
            print(f"   All {len(r_chat['sources'])} sources correctly filtered")
            print(f"   {PASS} Document-specific RAG filter works")
        else:
            print("   (no docs in DB to filter — skipping)")
    except Exception as e:
        print(f"   {FAIL} Filter test failed: {e}")
        errors.append("filter")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    if errors:
        print(f"  {FAIL} FAILED: {errors}")
        sys.exit(1)
    else:
        print(f"  {PASS} ALL PERSISTENCE TESTS PASSED")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
