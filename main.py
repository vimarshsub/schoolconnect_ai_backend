#!/usr/bin/env python3
"""
Main entry point for the SchoolConnect-AI Backend.
"""

import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("schoolconnect_ai")

# Create FastAPI app
app = FastAPI(
    title="SchoolConnect-AI Backend",
    description="Unified backend for SchoolConnect data ingestion and AI analysis",
    version="1.0.0",
)

# Add CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "[]")
try:
    import json
    origins = json.loads(cors_origins)
except:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import API routes
from src.api.routes import auth, ingestion, analysis, health

# Include API routes
app.include_router(health.router, tags=["health"])  # Removed prefix to expose health endpoint at /health
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["ingestion"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to SchoolConnect-AI Backend",
        "version": "1.0.0",
        "docs_url": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
