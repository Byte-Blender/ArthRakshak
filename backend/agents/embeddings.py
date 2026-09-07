# backend/agents/embeddings.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")

HF_EMBEDDING_URL = (
    "https://router.huggingface.co/"
    "hf-inference/models/"
    "sentence-transformers/all-MiniLM-L6-v2/"
    "pipeline/feature-extraction"
)


def embed_text(text: str) -> list:
    if not HF_API_KEY:
        raise ValueError("HF_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": text,
        "normalize": True,
    }

    response = requests.post(
        HF_EMBEDDING_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    embedding = response.json()

    # Single input returns one embedding vector.
    if isinstance(embedding, list) and embedding:
        if isinstance(embedding[0], list):
            embedding = embedding[0]

    if len(embedding) != 384:
        raise ValueError(
            f"Expected 384-dimensional embedding, got {len(embedding)}"
        )

    return embedding