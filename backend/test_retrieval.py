# backend/test_retrieval.py
from sqlalchemy import select
from db.database import SessionLocal
from db.models import FinancialDoc
from agents.embeddings import embed_text

def test_query(query: str, n: int = 3):
    db = SessionLocal()
    query_embedding = embed_text(query)
    results = db.scalars(
        select(FinancialDoc)
        .order_by(FinancialDoc.embedding.cosine_distance(query_embedding))
        .limit(n)
    ).all()
    db.close()

    print(f"\nQuery: {query}")
    for r in results:
        print(f"  [{r.source}] {r.content[:80]}...")

if __name__ == "__main__":
    test_query("how do I improve my credit score")
    test_query("government scheme for farmers")