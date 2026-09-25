"""
test_intelligence.py — Tests for Summarization, Extraction, and Comparison APIs (Phases 4 & 5).
"""

from __future__ import annotations

import sys, os, json, urllib.request, urllib.parse, time

BASE = "http://127.0.0.1:8000"
PASS = "[PASS]"
FAIL = "[FAIL]"

def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=60) as r:
        return json.loads(r.read())

def post(path: str, body: dict | None = None) -> dict:
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def upload_pdf(pdf_path: str, custom_filename: str = "") -> dict:
    boundary = "----DocIntelIntelBoundary"
    with open(pdf_path, "rb") as f:
        file_data = f.read()
    filename = custom_filename or os.path.basename(pdf_path)
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

def main():
    print("\nDocIntel AI — Phase 4 & 5: Intelligence & Comparison Tests\n")
    test_pdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_generated.pdf")

    # Upload doc 1
    doc1 = upload_pdf(test_pdf, "Policy_V1.pdf")
    doc1_id = doc1["document_id"]
    print(f"Uploaded Doc 1 (Policy_V1.pdf): {doc1_id}")

    # Upload doc 2
    doc2 = upload_pdf(test_pdf, "Policy_V2.pdf")
    doc2_id = doc2["document_id"]
    print(f"Uploaded Doc 2 (Policy_V2.pdf): {doc2_id}")

    # Test Summarize
    print("\n1. Testing POST /summarize/{document_id}...")
    res_sum = post(f"/summarize/{doc1_id}")
    assert "summary" in res_sum, "Summary key missing"
    assert len(res_sum["summary"]) > 50, "Summary too short"
    print(f"   Summary generated ({len(res_sum['summary'])} chars)")
    print(f"   Preview:\n{res_sum['summary'][:300]}...\n")
    print(f"{PASS} Summarize OK")

    # Test Extract
    print("\n2. Testing POST /extract/{document_id}...")
    res_ext = post(f"/extract/{doc1_id}")
    assert "extracted_data" in res_ext, "extracted_data key missing"
    ext_data = res_ext["extracted_data"]
    print(f"   Document Type: {ext_data.get('document_type')}")
    print(f"   Title/Subject: {ext_data.get('title_or_subject')}")
    print(f"   Parties: {ext_data.get('parties_or_entities')}")
    print(f"{PASS} Extract OK")

    # Test Compare
    print("\n3. Testing POST /compare...")
    res_comp = post("/compare", {"document_id_a": doc1_id, "document_id_b": doc2_id})
    assert "comparison" in res_comp, "comparison key missing"
    assert len(res_comp["comparison"]) > 50, "Comparison text too short"
    print(f"   Comparison generated ({len(res_comp['comparison'])} chars)")
    print(f"   Preview:\n{res_comp['comparison'][:300]}...\n")
    print(f"{PASS} Compare OK")

    print(f"\n{PASS} ALL Phase 4 & 5 Intelligence tests passed successfully!\n")

if __name__ == "__main__":
    main()
