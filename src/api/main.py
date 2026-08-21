"""
REST API Engine.
Exposes FastAPI endpoints for company, sector, screener, peer comparison, and valuation data.
Includes automatic Swagger documentation.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import RequestLoggingMiddleware
from src.api.routers import (
    companies,
    dna,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

# Initialize the FastAPI application with custom metadata
app = FastAPI(
    title="N100 Financial Intelligence API",
    version="1.0.0",
    description=(
        "REST API exposing financial analytics, screening, "
        "valuation, peer comparison, portfolio statistics, "
        "and company reports for the Nifty 100 universe."
    ),
)

# Enable CORS for frontend integration (allow all origins for internal use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable Request logging middleware to track method, path, response status, and duration
app.add_middleware(RequestLoggingMiddleware)

# Include modular routers under the /api/v1 prefix
app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")

# Include V2 routers
app.include_router(dna.router, prefix="/api/v2")


# ==========================================
# Root & Legacy/Compatibility Routes
# ==========================================


@app.get("/")
def read_root():
    """Root endpoint returning basic API info for backwards compatibility and checks."""
    return {
        "app": "Nifty 100 Financial Intelligence API",
        "docs": "/docs",
        "status": "healthy",
    }


@app.get("/api/company/{company_id}")
def get_company_ratios(company_id: str):
    """Legacy route to fetch company details (delegates to companies router)."""
    from src.api.routers.companies import get_company_details

    return get_company_details(company_id)


@app.get("/api/sector/{sector_name}")
def get_sector_data(sector_name: str):
    """Legacy route to fetch sector details (delegates to sectors router)."""
    from src.api.routers.sectors import get_sector_info

    return get_sector_info(sector_name)


@app.get("/api/screener/{preset_name}")
def run_screener_preset(preset_name: str):
    """Legacy route to run screener presets (delegates to screener router)."""
    from src.api.routers.screener import screen_companies

    return screen_companies(preset_name)


@app.get("/api/topperformers")
def get_top_performers():
    """Legacy route to fetch top performers (delegates to peers router)."""
    from src.api.routers.peers import get_peer_comparison

    res = get_peer_comparison(sector=None)
    return res["top_performers"]


@app.get("/api/peercomparison")
def get_peer_comparison_legacy():
    """Legacy route to fetch peer comparison (delegates to peers router)."""
    from src.api.routers.peers import get_peer_comparison

    res = get_peer_comparison(sector=None)
    return res["peer_comparison"]
