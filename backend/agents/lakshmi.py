# backend/agents/lakshmi.py
from sqlalchemy import select
from db.database import SessionLocal
from db.models import FinancialDoc
from agents.embeddings import embed_text
from agents.llm_client import get_llm_client


# ── RAG retrieval — unchanged, already confirmed working ──
def retrieve_context(query: str, n_results: int = 3) -> str:
    query_embedding = embed_text(query)
    db = SessionLocal()
    try:
        results = db.scalars(
            select(FinancialDoc)
            .order_by(FinancialDoc.embedding.cosine_distance(query_embedding))
            .limit(n_results)
        ).all()
        return "\n\n".join([r.content for r in results])
    finally:
        db.close()


# ── System prompt ─────────────────────────────────────────
SYSTEM_PROMPT = """You are Lakshmi, a warm and friendly financial advisor for everyday Indians.

Your rules, follow them strictly:
1. Explain finances in simple, everyday language. Avoid jargon. If you must use a term, explain it immediately.
2. Always relate advice to the user's actual situation and life stage.
3. End EVERY response with exactly ONE clear next step the user can take today.
4. NEVER recommend any specific financial product, fund, stock, or company by name.
5. If someone seems to be in financial distress, acknowledge their feelings first before giving advice.
6. Be judgment-free. Many users come from low-income backgrounds. Never make them feel bad about their financial situation.
7. Base your answer on the provided context where relevant. If the context doesn't cover the question, say so honestly rather than guessing.
"""

PROMPT_TEMPLATE = """{system}

Relevant knowledge:
{context}

User question: {question}"""


# ── Guardrail post-check ──────────────────────────────────
FLAGGED_PHRASES = [
    "I recommend", "you should buy", "invest in",
    "purchase", "sign up for", "download this app"
]

def apply_guardrail(response: str) -> str:
    for phrase in FLAGGED_PHRASES:
        if phrase.lower() in response.lower():
            response += "\n\nNote: Lakshmi provides financial education only and does not recommend specific products."
            break
    return response


# ── Main agent function — backend-agnostic ────────────────
def ask_lakshmi(message: str) -> dict:
    context = retrieve_context(message)

    prompt = PROMPT_TEMPLATE.format(
        system=SYSTEM_PROMPT,
        context=context,
        question=message
    )

    client = get_llm_client()
    raw_response = client.generate(prompt, max_tokens=800, temperature=0.3)
    final_response = apply_guardrail(raw_response)

    return {
        "reply": final_response,
        "context_used": context[:200] + "..." if context else "no relevant context found",
        "agent": "lakshmi"
    }