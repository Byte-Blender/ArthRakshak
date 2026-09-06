# data/seed/ingest_pdfs.py
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../backend"))

from db.database import SessionLocal
from db.models import FinancialDoc, init_db
from agents.embeddings import embed_text
from agents.document_ingest import process_pdf

RAW_DOCS_DIR = os.path.join(os.path.dirname(__file__), "../raw_docs")

def ingest_all_pdfs(clear_existing_pdf_chunks: bool = True):
    init_db()
    db = SessionLocal()
    try:
        pdf_files = [f for f in os.listdir(RAW_DOCS_DIR) if f.lower().endswith(".pdf")]

        if not pdf_files:
            print(f"No PDFs found in {RAW_DOCS_DIR}. Drop some .pdf files there first.")
            return

        for filename in pdf_files:
            filepath = os.path.join(RAW_DOCS_DIR, filename)
            print(f"\nProcessing {filename}...")

            if clear_existing_pdf_chunks:
                deleted = db.query(FinancialDoc).filter_by(source=filename).delete()
                if deleted:
                    print(f"  Cleared {deleted} existing chunks from this file")

            chunks = process_pdf(filepath)
            print(f"  Extracted {len(chunks)} chunks")

            for chunk in chunks:
                embedding = embed_text(chunk)
                db.add(FinancialDoc(content=chunk, embedding=embedding, source=filename))

            db.commit()
            print(f"  Stored {len(chunks)} chunks from {filename}")

        total = db.query(FinancialDoc).count()
        print(f"\nDone. financial_docs now has {total} total chunks.")

    finally:
        db.close()

if __name__ == "__main__":
    ingest_all_pdfs()