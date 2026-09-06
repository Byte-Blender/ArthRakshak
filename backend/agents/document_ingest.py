# backend/agents/document_ingest.py
import pdfplumber
import os
import re

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts all text from a PDF, page by page."""
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n\n".join(full_text)


def clean_text(text: str) -> str:
    """Basic cleanup — collapse excess whitespace, strip page artifacts."""
    text = re.sub(r'\n{3,}', '\n\n', text)   # collapse 3+ newlines to 2
    text = re.sub(r'[ \t]{2,}', ' ', text)    # collapse repeated spaces/tabs
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Splits text into overlapping chunks at sentence boundaries where possible.
    chunk_size and overlap are measured in characters.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += (" " if current_chunk else "") + sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # start new chunk, carrying overlap from the end of the previous one
            # overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + " " + sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    # filter out tiny fragments that aren't useful as standalone retrievable chunks
    chunks = [c for c in chunks if len(c) > 40]
    return chunks


def process_pdf(pdf_path: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Full pipeline: PDF -> cleaned text -> chunks. Returns list of chunk strings."""
    raw_text = extract_text_from_pdf(pdf_path)
    cleaned = clean_text(raw_text)
    chunks = chunk_text(cleaned, chunk_size, overlap)
    return chunks