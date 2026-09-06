# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from api.saheli import router as saheli_router
from contextlib import asynccontextmanager
from agents.llm_client import get_llm_client
import os

@asynccontextmanager
async def lifespan(app):
    print("Preloading model...")
    get_llm_client()  # loads once, cached globally
    yield

app = FastAPI(title="ArthSaathi API", version="0.3.0", lifespan=lifespan)

# FRONTEND_URL should be your deployed frontend's origin, e.g.
# https://arthsaathi.vercel.app (no trailing slash). localhost:5173
# stays allowed so local dev keeps working alongside the deployed version.
allowed_origins = ["http://localhost:5173"]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(saheli_router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ArthSaathi"}