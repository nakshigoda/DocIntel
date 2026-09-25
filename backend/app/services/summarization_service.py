"""
summarization_service.py — Document summarization service using LLM.

Provides executive summaries, key points, important clauses, risks, and action items.
"""

from __future__ import annotations

import logging
from app.services.database import documents_collection
from app.services.llm_service import _client, GROQ_MODEL, _strip_thinking
from app.services.pdf_service import extract_pages
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_SUMMARIZE_SYSTEM_PROMPT = """\
You are an expert enterprise document analyst.
Your task is to provide a comprehensive, structured summary of the document context provided.

Structure your response into clear markdown sections:
### Executive Summary
Brief high-level overview of the document (2-4 sentences).

### Key Points
- Bullets of main information or findings.

### Important Clauses & Terms
- Summary of essential legal, technical, or operational conditions.

### Identified Risks & Considerations
- Potential risks, liabilities, or notable caveats.

### Action Items & Next Steps
- Actionable steps, deadlines, or required follow-ups mentioned in the text.

If any section has no relevant details in the context, explicitly state "None identified in the document."
Do not invent information outside the provided text.
"""

def summarize_document(document_id: str) -> dict:
    """
    Generate a structured summary for a document stored in MongoDB.
    """
    doc = documents_collection.find_one({"document_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    filepath = doc.get("filepath")
    if not filepath:
        raise HTTPException(status_code=400, detail="Document file path missing.")

    # Extract text
    extraction = extract_pages(filepath)
    full_text = "\n\n".join([p["text"] for p in extraction["pages"] if p["text"]])

    if not full_text.strip():
        return {
            "document_id": document_id,
            "filename": doc.get("filename"),
            "summary": "Document contains no readable text.",
        }

    # Limit prompt size for model context window if doc is huge (take up to 15k chars for summary)
    context_text = full_text[:15000]

    user_prompt = f"DOCUMENT TITLE: {doc.get('filename')}\n\nDOCUMENT TEXT:\n{context_text}\n\nProvide the structured document summary."

    logger.info("Generating summary for document %s using model %s", document_id, GROQ_MODEL)

    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SUMMARIZE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    raw_content = response.choices[0].message.content or ""
    clean_summary = _strip_thinking(raw_content)

    return {
        "document_id": document_id,
        "filename": doc.get("filename"),
        "page_count": extraction["page_count"],
        "word_count": extraction["word_count"],
        "summary": clean_summary,
    }
