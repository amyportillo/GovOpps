# api.py
# Main API file - all the endpoints we use are defined here
# FastAPI makes it easy to set up endpoints and it gives us auto-generated docs at /docs
#
# Run with: uvicorn api:app --reload --port 8000
# The reload flag is helpful because it restarts the server when I save files

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from database import get_db, init_db, Agency, Contract, ApiFetchAudit
from schemas import (
    ContractResponse,
    VendorResponse,
    ApplicationResponse,
    HealthResponse,
)


# Create the FastAPI app instance
# The title, version, and description show up in the docs
app = FastAPI(
    title="Gov Contracts API",
    version="1.0.0",
    description="Exposes government contract opportunities fetched from SAM.gov. Run python etl.py first to populate the database.",
)


# Runs when the server starts up
# Makes sure all the database tables exist before we start handling requests
@app.on_event("startup")
def on_startup():
    init_db()


# GET /contracts endpoint
# Returns contracts with their agency names included
@app.get(
    "/contracts",
    response_model=list[ContractResponse],
    summary="Retrieve contract opportunities",
    tags=["Contracts"],
)
def get_contracts(
    # URL params - limit how many results come back, filter by agency if needed
    limit:     int               = Query(default=100, ge=1, le=1000, description="Max rows to return"),
    agency_id: Optional[int]     = Query(default=None, description="Filter by agency ID"),
    # Get database session from FastAPI's dependency injection
    db:        Session           = Depends(get_db),
):
    # Query contracts and join with agency table to get the agency name
    query = (
        db.query(
            Contract.id,
            Contract.notice_id,
            Contract.title,
            Contract.solicitation_number,
            Contract.agency_id,
            Agency.name.label("agency_name"),
            Contract.posted_date,
            Contract.created_at,
        )
        .join(Agency, Agency.id == Contract.agency_id)
    )

    # Filter by agency if the user specified one
    if agency_id is not None:
        query = query.filter(Contract.agency_id == agency_id)

    # Execute query, sort by newest first
    rows = query.order_by(Contract.created_at.desc()).limit(limit).all()

    # Convert database rows to response format
    return [
        ContractResponse(
            id=                  row.id,
            notice_id=           row.notice_id,
            title=               row.title,
            solicitation_number= row.solicitation_number,
            agency_id=           row.agency_id,
            agency_name=         row.agency_name,
            posted_date=         row.posted_date,
            created_at=          row.created_at,
        )
        for row in rows
    ]


# GET /vendors endpoint
# Lists all agencies and counts how many contracts each one has
@app.get(
    "/vendors",
    response_model=list[VendorResponse],
    summary="Retrieve vendors / agencies",
    tags=["Vendors"],
)
def get_vendors(
    # Optional search filter - case insensitive
    search: Optional[str] = Query(default=None, description="Case-insensitive name filter"),
    db:     Session       = Depends(get_db),
):
    # Query agencies with contract count - use outerjoin so agencies with 0 contracts still show up
    query = (
        db.query(
            Agency.id,
            Agency.name,
            func.count(Contract.id).label("contract_count"),
            Agency.created_at,
        )
        .outerjoin(Contract, Contract.agency_id == Agency.id)
        .group_by(Agency.id, Agency.name, Agency.created_at)
    )

    # Apply search filter if provided
    if search:
        query = query.filter(Agency.name.ilike(f"%{search}%"))

    # Sort by most contracts first
    rows = query.order_by(func.count(Contract.id).desc()).all()

    # Convert to response format
    return [
        VendorResponse(
            id=             row.id,
            name=           row.name,
            contract_count= row.contract_count,
            created_at=     row.created_at,
        )
        for row in rows
    ]


# GET /applications endpoint
# Returns the history of ETL runs - shows when we fetched data and if it worked
@app.get(
    "/applications",
    response_model=list[ApplicationResponse],
    summary="Retrieve ETL application run history",
    tags=["Applications"],
)
def get_applications(
    # Let users choose how many results to get
    limit: int     = Query(default=50, ge=1, le=500, description="Max rows to return"),
    db:    Session = Depends(get_db),
):
    # Get audit records, newest first
    rows = (
        db.query(ApiFetchAudit)
        .order_by(ApiFetchAudit.fetched_at.desc())
        .limit(limit)
        .all()
    )

    # Convert to response format
    return [
        ApplicationResponse(
            id=          row.id,
            source_name= row.source_name,
            status_code= row.status_code,
            was_success= row.was_success,
            posted_from= row.posted_from,
            posted_to=   row.posted_to,
            fetched_at=  row.fetched_at,
        )
        for row in rows
    ]


# GET /health endpoint
# Simple status check to see if the API is running
@app.get("/health", response_model=HealthResponse, include_in_schema=False)
def health():
    return HealthResponse(status="healthy", timestamp=datetime.now(timezone.utc))