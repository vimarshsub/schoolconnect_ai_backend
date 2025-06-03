#!/usr/bin/env python3
"""
Main entry point for the SchoolConnect-AI Backend.
"""

import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from src.api import setup_middleware

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

# Add CORS middleware with more permissive defaults
cors_origins = os.getenv("CORS_ORIGINS", "[]")
try:
    import json
    origins = json.loads(cors_origins)
    logger.info(f"Configured CORS origins: {origins}")
    if not origins:  # If empty list, use wildcard
        logger.warning("No CORS origins specified, defaulting to allow all origins")
        origins = ["*"]
except Exception as e:
    logger.warning(f"Error parsing CORS_ORIGINS, defaulting to allow all origins: {str(e)}")
    origins = ["*"]

# Always include Lovable domain explicitly
lovable_domain = "https://d542924f-201b-48c7-b9de-4b6f2cdb8ab2.lovableproject.com"
if lovable_domain not in origins and "*" not in origins:
    origins.append(lovable_domain)
    logger.info(f"Added Lovable domain to CORS origins: {lovable_domain}")

logger.info(f"Final CORS origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up authentication middleware
setup_middleware(app)

# Add a direct health check endpoint at the root level
@app.get("/health")
async def health_check():
    """Simple health check endpoint that returns a 200 OK status."""
    return {"status": "healthy"}

# Import API routes
from src.api.routes import auth, ingestion, analysis, health

# Include API routes
app.include_router(health.router, tags=["health"])  # Health router still included for backward compatibility
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
    # Determine if we're in development mode for reload setting
    is_dev = os.getenv("ENVIRONMENT", "production").lower() == "development" or os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=is_dev)
