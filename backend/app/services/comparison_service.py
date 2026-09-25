"""
comparison_service.py — Document comparison service using LLM.

Compares two uploaded documents to highlight additions, removals, modified clauses, and key differences.
"""

from __future__ import annotations

import logging
from app.services.database import documents_collection
from app.services.llm_service import _client, GROQ_MODEL, _strip_thinking
from app.services.pdf_service import extract_pages
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_COMPARISON_SYSTEM_PROMPT = """\
You are an expert contract and enterprise document comparison analyst.
Compare DOCUMENT A and DOCUMENT B provided below.

Structure your analysis into clear markdown sections:
### Executive Comparison Summary
Overview of how the two documents relate (e.g., version update, different policies, competing proposals) and the main takeaways.

### Key Additions (Present in B, Missing in A)
- Detail clauses, terms, or sections added in Document B.

### Key Removals (Present in A, Missing in B)
- Detail clauses, terms, or sections omitted in Document B.

### Modified Terms & Differences
- Detailed breakdown of changed numbers, dates, payment terms, responsibilities, or legal conditions.

### Risk & Operational Impact Assessment
- Summary of practical implications or risks arising from these differences.

Be factual and specific, referencing document context accurately.
"""

def compare_documents(document_id_a: str, document_id_b: str) -> dict:
    """
    Compare two documents stored in MongoDB and return a structured diff analysis.
    """
    doc_a = documents_collection.find_one({"document_id": document_id_a})
    if not doc_a:
        raise HTTPException(status_code=404, detail=f"Document A '{document_id_a}' not found.")

    doc_b = documents_collection.find_one({"document_id": document_id_b})
    if not doc_b:
        raise HTTPException(status_code=404, detail=f"Document B '{document_id_b}' not found.")

    path_a = doc_a.get("filepath")
    path_b = doc_b.get("filepath")
    if not path_a or not path_b:
        raise HTTPException(status_code=400, detail="One or both document files are missing from disk.")

    ext_a = extract_pages(path_a)
    ext_b = extract_pages(path_b)

    text_a = "\n\n".join([p["text"] for p in ext_a["pages"] if p["text"]])[:10000]
    text_b = "\n\n".join([p["text"] for p in ext_b["pages"] if p["text"]])[:10000]

    user_prompt = (
        f"--- DOCUMENT A ({doc_a.get('filename')}) ---\n"
        f"{text_a}\n\n"
        f"--- DOCUMENT B ({doc_b.get('filename')}) ---\n"
        f"{text_b}\n\n"
        "Provide a comprehensive document comparison analysis."
    )

    logger.info("Comparing document %s vs %s using model %s", document_id_a, document_id_b, GROQ_MODEL)

    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _COMPARISON_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=2000,
    )

    raw_content = response.choices[0].message.content or ""
    clean_comparison = _strip_thinking(raw_content)

    return {
        "document_a": {
            "document_id": document_id_a,
            "filename": doc_a.get("filename"),
            "page_count": ext_a["page_count"],
        },
        "document_b": {
            "document_id": document_id_b,
            "filename": doc_b.get("filename"),
            "page_count": ext_b["page_count"],
        },
        "comparison": clean_comparison,
    }
