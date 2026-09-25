"""
test_endpoints.py — Live endpoint tests against a running server.

Usage (server must already be running on http://127.0.0.1:8000):
    venv\\Scripts\\python tests/test_endpoints.py [pdf_path]

If no pdf_path given, a synthetic PDF from tests/test_generated.pdf is used.
"""
from __future__ import annotations

import sys
import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

PASS = "[PASS]"
FAIL = "[FAIL]"


def _get(path: str) -> dict:
    url = BASE_URL + path
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read())


def _post_json(path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _upload_pdf(pdf_path: str) -> dict:
    """Multipart upload using stdlib only."""
    boundary = "----DocIntelBoundary1234567890"
    with open(pdf_path, "rb") as f:
        file_data = f.read()
    filename = os.path.basename(pdf_path)
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        BASE_URL + "/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def _banner(title: str):
    print(f"\n{'='*55}\n  {title}\n{'='*55}")


def test_health():
    _banner("GET /health")
    r = _get("/health")
    assert r.get("status") == "ok", f"Unexpected: {r}"
    print(f"  response: {r}")
    print(f"{PASS} Health OK")


def test_root():
    _banner("GET /")
    r = _get("/")
    assert r.get("version") == "2.0.0", f"Unexpected: {r}"
    print(f"  response: {r}")
    print(f"{PASS} Root OK")


def test_upload(pdf_path: str) -> str:
    _banner(f"POST /upload  ({os.path.basename(pdf_path)})")
    r = _upload_pdf(pdf_path)
    print(f"  document_id:  {r.get('document_id')}")
    print(f"  status:       {r.get('status')}")
    print(f"  page_count:   {r.get('page_count')}")
    print(f"  word_count:   {r.get('word_count')}")
    print(f"  chunk_count:  {r.get('chunk_count')}")
    print(f"  is_scanned:   {r.get('is_scanned')}")
    print(f"  message:      {r.get('message')}")
    assert r.get("status") == "processed", f"Expected 'processed', got: {r}"
    assert r.get("chunk_count", 0) > 0, "No chunks stored"
    print(f"{PASS} Upload OK  (doc_id={r['document_id']})")
    return r["document_id"]


def test_search(query: str, doc_id: str = "all"):
    _banner(f"GET /search?query={query!r}")
    path = f"/search?query={urllib.parse.quote(query)}&document_id={doc_id}"
    r = _get(path)
    print(f"  total results: {r.get('total')}")
    for hit in r.get("results", [])[:3]:
        print(
            f"  -> [{hit['document_name']}] p.{hit['page_number']}  "
            f"score={hit['score']}  '{hit['snippet'][:60]}...'"
        )
    assert isinstance(r.get("results"), list), "results should be a list"
    print(f"{PASS} Search OK")
    return r


def test_chat(query: str, doc_id: str = "all"):
    _banner(f"GET /chat?query={query!r}")
    path = f"/chat?query={urllib.parse.quote(query)}&document_id={doc_id}"
    r = _get(path)
    print(f"  answer: {r.get('answer','')[:200]}")
    print(f"  sources: {len(r.get('sources', []))}")
    for src in r.get("sources", [])[:2]:
        print(f"    [{src['document_name']}] p.{src['page_number']} score={src['score']}")
    assert "answer" in r, "Missing 'answer' key"
    print(f"{PASS} Chat OK")


def test_rejection():
    _banner("POST /upload with non-PDF (rejection test)")
    boundary = "----DocIntelBoundaryXYZ"
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"fake.txt\"\r\n"
        f"Content-Type: text/plain\r\n\r\n"
        f"This is not a PDF\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        BASE_URL + "/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        print(f"{FAIL} Should have been rejected but wasn't")
    except urllib.error.HTTPError as e:
        assert e.code == 400, f"Expected 400, got {e.code}"
        print(f"  Correctly rejected with HTTP {e.code}")
        print(f"{PASS} Rejection OK")


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None

    # Use test_generated.pdf if no real PDF provided
    if pdf_path is None:
        generated = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_generated.pdf"
        )
        if not os.path.exists(generated):
            print("No PDF provided and test_generated.pdf not found.")
            print("Run test_pipeline.py first to generate it, or pass a PDF path.")
            sys.exit(1)
        pdf_path = generated

    print("\nDocIntel AI — Live Endpoint Tests")
    print(f"Server: {BASE_URL}")
    print(f"PDF:    {pdf_path}\n")

    errors = []

    for name, fn in [("health", test_health), ("root", test_root)]:
        try:
            fn()
        except Exception as e:
            print(f"{FAIL} {name}: {e}")
            errors.append(name)

    try:
        doc_id = test_upload(pdf_path)
        time.sleep(1)  # small pause to let ChromaDB flush
        test_search("document intelligence retrieval", doc_id)
        test_search("document intelligence retrieval", "all")
        test_chat("What is this document about?", doc_id)
    except Exception as e:
        import traceback
        print(f"{FAIL} {e}")
        traceback.print_exc()
        errors.append("upload/search/chat")

    try:
        test_rejection()
    except Exception as e:
        print(f"{FAIL} rejection: {e}")
        errors.append("rejection")

    print(f"\n{'='*55}")
    if errors:
        print(f"  {FAIL} FAILED: {errors}")
        sys.exit(1)
    else:
        print(f"  {PASS} All endpoint tests passed!")
    print(f"{'='*55}\n")
