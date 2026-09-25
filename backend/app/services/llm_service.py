"""
llm_service.py — LLM answer generation for DocIntel AI.

Uses Groq API for fast, free cloud inference.
Model is read from config / .env (GROQ_MODEL) so it can be changed
without touching code.

Supported model format: any model ID valid for your Groq account.
Set in backend/.env:
    GROQ_MODEL=qwen/qwen3.8-27b        # thinking model (default)
    GROQ_MODEL=openai/gpt-oss-20b      # non-thinking alternative

Thinking models (e.g. Qwen) wrap internal reasoning in <think>…</think>
blocks.  These are stripped before the answer is returned — the frontend
never sees them.
"""

from __future__ import annotations

import re
import logging

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

# ── Validation ────────────────────────────────────────────────────────────────
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. "
        "Add it to backend/.env before starting the server."
    )

_client = Groq(api_key=GROQ_API_KEY)

# ── Prompts ───────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are a precise document Q&A assistant for an enterprise document intelligence system.

Your rules:
1. Answer ONLY using the RETRIEVED DOCUMENT CONTEXT provided.  \
Do NOT use any outside knowledge or facts not present in the context.
2. If the answer is not present in the context, respond exactly:
   "This information was not found in the provided documents."
3. Keep answers concise, accurate, and well-structured.
4. When citing information, reference the source document and page number \
as shown in the context headers (e.g. [Source: Filename.pdf, Page 3]).
5. If multiple sources support the answer, mention each one.
6. Do NOT invent facts, figures, dates, names, or clauses that are not \
in the context.
7. Do not repeat the question back to the user."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_thinking(text: str) -> str:
    """
    Remove reasoning/chain-of-thought blocks emitted by thinking models.

    Handles two common formats:
      • Qwen-style:  <think>…</think>
      • Plain:       text that begins before an answer marker

    Strategy:
      1. Remove full <think>…</think> blocks (greedy, dotall).
      2. If the remaining text is empty but the raw text is non-empty,
         fall back to taking everything after the last </think>.
      3. Strip leading/trailing whitespace.
    """
    if "<think>" not in text:
        return text.strip()

    # Remove all <think>…</think> blocks
    stripped = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    stripped = stripped.strip()

    # Fallback: if stripping left nothing, take everything after </think>
    if not stripped:
        after = text.rsplit("</think>", 1)[-1]
        stripped = after.strip()

    # Final safety: if STILL empty, log and return a safe message
    if not stripped:
        logger.warning(
            "LLM response contained only <think> content — nothing left to return."
        )
        return "The model could not produce a final answer from the provided context."

    return stripped


# ── Public API ────────────────────────────────────────────────────────────────

def generate_answer(context: str, query: str) -> str:
    """
    Generate a grounded answer from retrieved document context.

    Args:
        context: Pre-formatted chunk text with source headers, e.g.:
                     [Source: Report.pdf, Page 3]
                     The company reported revenue of $2.4B in Q3 ...
                 Multiple chunks separated by "\\n\\n---\\n\\n".
        query:   The user's natural-language question.

    Returns:
        A clean answer string.  Any <think> content is stripped.
        If context is empty, returns a safe "not found" message without
        calling the LLM.
    """
    if not context or not context.strip():
        return "No relevant information was found in the uploaded documents."

    user_message = (
        f"RETRIEVED DOCUMENT CONTEXT:\n{context}\n\n"
        f"USER QUESTION:\n{query}\n\n"
        "Provide a clear, grounded answer based only on the above context."
    )

    logger.info(
        "Calling Groq model '%s' | query: %s",
        GROQ_MODEL,
        query[:80],
    )

    response = _client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.1,   # low = factual, minimal hallucination
        max_tokens=1024,
    )

    raw_content: str = response.choices[0].message.content or ""
    answer = _strip_thinking(raw_content)

    logger.info(
        "Groq response: %d raw chars → %d final chars",
        len(raw_content),
        len(answer),
    )
    return answer