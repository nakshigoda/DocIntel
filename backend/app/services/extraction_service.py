"""
extraction_service.py — Structured information extraction service using LLM.

Extracts structured JSON fields (parties, dates, financial terms, obligations, etc.) from enterprise documents.
"""

from __future__ import annotations

import json
import re
import logging
from app.services.database import documents_collection
from app.services.llm_service import _client, GROQ_MODEL, _strip_thinking
from app.services.pdf_service import extract_pages
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_EXTRACTION_SYSTEM_PROMPT = """\
You are an enterprise information extraction AI.
Extract key structured attributes from the document text provided.

Respond ONLY with a valid JSON object matching the following structure:
{
  "document_type": "Contract / Invoice / Policy / Report / Technical / Other",
  "title_or_subject": "Brief subject or title",
  "parties_or_entities": ["Entity 1", "Entity 2"],
  "important_dates": [
    {"date": "YYYY-MM-DD or string", "description": "e.g., Effective date, Expiration date, Deadline"}
  ],
  "financial_terms": [
    {"term": "Amount or Payment Rule", "details": "Description"}
  ],
  "obligations_and_duties": ["Obligation 1", "Obligation 2"],
  "key_clauses": [
    {"type": "Termination / Renewal / Liability / Confidentiality / etc.", "summary": "Summary of clause"}
  ],
  "summary_entities": ["Key Person", "Key Location", "Key System"]
}

Rules:
1. Output MUST be strictly valid JSON without markdown codeblocks or unescaped quotes.
2. If a field cannot be found in the document, use an empty list [] or null.
3. Do not invent or extrapolate fields.
"""

def extract_structured_info(document_id: str) -> dict:
    """
    Extract key structured information from a document stored in MongoDB.
    """
    doc = documents_collection.find_one({"document_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    filepath = doc.get("filepath")
    if not filepath:
        raise HTTPException(status_code=400, detail="Document file path missing.")

    extraction = extract_pages(filepath)
    full_text = "\n\n".join([p["text"] for p in extraction["pages"] if p["text"]])

    if not full_text.strip():
        return {
            "document_id": document_id,
            "filename": doc.get("filename"),
            "extracted_data": {},
            "raw_text_length": 0
        }

    context_text = full_text[:15000]

    user_prompt = f"DOCUMENT FILENAME: {doc.get('filename')}\n\nDOCUMENT TEXT:\n{context_text}\n\nExtract structured JSON."

    logger.info("Extracting structured info for document %s using model %s", document_id, GROQ_MODEL)

    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=1500,
    )

    raw_content = response.choices[0].message.content or ""
    clean_text = _strip_thinking(raw_content)

    # Clean markdown json fencing if present
    clean_json_str = re.sub(r"^```json\s*", "", clean_text, flags=re.MULTILINE)
    clean_json_str = re.sub(r"```$", "", clean_json_str, flags=re.MULTILINE).strip()

    try:
        extracted_json = json.loads(clean_json_str)
    except Exception as e:
        logger.warning("Failed to parse LLM response as JSON: %s. Raw text: %s", e, clean_text)
        extracted_json = {
            "parse_error": "Could not parse response as JSON",
            "raw_response": clean_text
        }

    return {
        "document_id": document_id,
        "filename": doc.get("filename"),
        "extracted_data": extracted_json
    }
