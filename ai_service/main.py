"""Main FastAPI application for the Tax Explainer AI Service."""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Tax Explainer AI Service")
    logger.info(f"IRC data path: {Path(__file__).parent.parent.parent / 'docs' / 'tax-law' / 'irc'}")
    yield
    # Shutdown
    logger.info("Shutting down Tax Explainer AI Service")


app = FastAPI(
    title="Tax Explainer AI Service",
    description="""
    AI-powered service for explaining tax form line items with citations to
    Internal Revenue Code (IRC) sections and Treasury Regulations.

    ## Features

    - **Line Item Explanations**: Get plain-English explanations for any form line
    - **IRC Search**: Search the Internal Revenue Code semantically
    - **Form Cross-References**: See IRC sections related to each form
    - **Chat**: Conversational tax assistance
    - **Document Scanning**: OCR for W-2, 1099, and other tax documents
    - **Brokerage Import**: CSV import from major brokerages for Form 8949
    - **Cost Basis Tracking**: Multi-year investment tracking
    - **What-If Scenarios**: Tax impact analysis for financial decisions
    - **Prior Year Import**: Import prior year data with carry-forward
    - **Interview Wizard**: 40+ question guided interview with skip logic
    - **Tax Planning Calculator**: Marginal/effective rate calculation
    - **Push Notifications**: Quarterly estimated tax and deadline reminders

    ## Data Sources

    - 2,204 IRC sections from Title 26 USC
    - Treasury Regulations (26 CFR)
    - Form-IRC cross-reference mappings
    - IRS Direct File fact graph mappings
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # UsTaxes dev
        "http://localhost:5173",  # Vite dev
        "http://localhost:8080",  # direct-file-easy-webui
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routes
from .routes.explainer import router as explainer_router
from .routes.documents import router as documents_router
from .routes.planning import router as planning_router

app.include_router(explainer_router)
app.include_router(documents_router)
app.include_router(planning_router)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "service": "Tax Explainer AI Service",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
