# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.saheli import router as saheli_router

import os


app = FastAPI(
    title="ArthSaathi API",
    version="0.3.0"
)


# Allowed frontend origins
# No trailing slash in origins.
allowed_origins = [
    "http://localhost:5173",
    "https://arthrakshak-three.vercel.app",
    "https://arthrakshak-aia271xby-shreyanshgupta1579-9505s-projects.vercel.app",
]


# Optional Render environment variable
frontend_url = os.getenv("FRONTEND_URL")

if frontend_url:
    frontend_url = frontend_url.rstrip("/")
    allowed_origins.append(frontend_url)


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API routes
app.include_router(router)
app.include_router(saheli_router)


# Health check
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ArthSaathi"
    }