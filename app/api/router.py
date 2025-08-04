"""
Main API router that includes all endpoint routers
"""
from fastapi import APIRouter
from app.api.endpoints import companies, leads, auth, analytics, ingestion, enrichment, scoring, export, notifications, outreach

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    companies.router,
    prefix="/companies",
    tags=["Companies"]
)

api_router.include_router(
    leads.router,
    prefix="/leads",
    tags=["Leads"]
)

api_router.include_router(
    ingestion.router,
    prefix="/ingestion",
    tags=["Data Ingestion"]
)

api_router.include_router(
    enrichment.router,
    prefix="/enrichment",
    tags=["Lead Enrichment"]
)

api_router.include_router(
    scoring.router,
    prefix="/scoring",
    tags=["Lead Scoring"]
)

api_router.include_router(
    export.router,
    prefix="/export",
    tags=["Data Export"]
)

api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["Notifications"]
)

api_router.include_router(
    outreach.router,
    prefix="/outreach",
    tags=["Outreach"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)