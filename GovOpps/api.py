# api.py
# FastAPI app with all three data endpoints plus a health check.
# Returns JSON — this is the machine-readable side of the project.
#
# Start with:  python run.py api
# Then visit:  http://localhost:8000/docs  for interactive documentation

from datetime import datetime, timezone
from typing import Optional
# depends is a FastAPI feature that allows you to declare dependencies for your path operation functions.
# query defines and validates URL parameters
from fastapi import FastAPI, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db, init_db, Agency, Contract, ApiFetchAudit
from schemas import ContractResponse, VendorResponse, ApplicationResponse, HealthResponse


# Create the FastAPI app. The title and description show up on the /docs page.
app = FastAPI(
    title="Gov Contracts API",
    version="1.0.0",
    description="Government contract opportunities from SAM.gov. Run `python run.py etl` first to load data.",
)


@app.on_event("startup")
def on_startup():
    # This runs once automatically when the server starts.
    # It adds any missing DB columns (the notice_id and solicitation_number migration).
    # Safe to run every time — uses "IF NOT EXISTS" so it won't crash if they already exist.
    init_db()


@app.get("/contracts", response_model=list[ContractResponse], tags=["Contracts"])
def get_contracts(
    # Query parameters are values passed in the URL like: /contracts?limit=50&agency_id=3
    # ge=1 means "must be >= 1", le=1000 means "must be <= 1000".
    # FastAPI validates these automatically and returns a 422 error if they're out of range.
    limit:     int           = Query(default=100, ge=1, le=1000, description="Max rows to return"),
    agency_id: Optional[int] = Query(default=None, description="Filter by agency ID"),

    # Depends(get_db) is dependency injection — FastAPI calls get_db() for us,
    # gets a live database session, and passes it in. We never call get_db() ourselves.
    db:        Session       = Depends(get_db),
):
    # Build a query that JOINs contracts with agencies so we can include agency_name
    # in the response without making a second query.
    query = (
        db.query(
            Contract.contract_id,
            Contract.notice_id,
            Contract.title,
            Contract.solicitation_number,
            Contract.agency_id,
            Agency.agency_name,
            Contract.posted_date,
        )
        .join(Agency, Agency.agency_id == Contract.agency_id)
    )

    # Optionally filter by agency — only applied if the caller passed ?agency_id=...
    if agency_id is not None:
        query = query.filter(Contract.agency_id == agency_id)

    # Order newest first, then cap the result set to the requested limit.
    rows = query.order_by(Contract.contract_id.desc()).limit(limit).all()

    # Convert each raw DB row into a ContractResponse Pydantic object.
    # FastAPI then serializes these to JSON automatically.
    return [
        ContractResponse(
            contract_id=         row.contract_id,
            notice_id=           row.notice_id,
            title=               row.title,
            solicitation_number= row.solicitation_number,
            agency_id=           row.agency_id,
            agency_name=         row.agency_name,
            posted_date=         row.posted_date,
        )
        for row in rows
    ]


@app.get("/vendors", response_model=list[VendorResponse], tags=["Vendors"])
def get_vendors(
    # Optional text search — filters agencies whose name contains the search string.
    # Example: /vendors?search=defense  returns only defense-related agencies.
    search: Optional[str] = Query(default=None, description="Filter by agency name (case-insensitive)"),
    db:     Session       = Depends(get_db),
):
    # Count how many contracts each agency has using a GROUP BY + COUNT.
    # outerjoin means agencies with zero contracts still appear in the results.
    query = (
        db.query(
            Agency.agency_id,
            Agency.agency_name,
            func.count(Contract.contract_id).label("contract_count"),  # computed column
        )
        .outerjoin(Contract, Contract.agency_id == Agency.agency_id)
        .group_by(Agency.agency_id, Agency.agency_name)
    )

    # ilike is case-insensitive LIKE — %search% means "contains search anywhere in the name"
    if search:
        query = query.filter(Agency.agency_name.ilike(f"%{search}%"))

    # Sort by most contracts first so the busiest agencies appear at the top
    rows = query.order_by(func.count(Contract.contract_id).desc()).all()

    return [
        VendorResponse(
            agency_id=      row.agency_id,
            agency_name=    row.agency_name,
            contract_count= row.contract_count,
        )
        for row in rows
    ]


@app.get("/applications", response_model=list[ApplicationResponse], tags=["Applications"])
def get_applications(
    limit: int     = Query(default=50, ge=1, le=500, description="Max rows to return"),
    db:    Session = Depends(get_db),
):
    # Returns the history of ETL runs — when they ran, whether they succeeded,
    # and what date range was fetched. Newest runs appear first.
    rows = (
        db.query(ApiFetchAudit)
        .order_by(ApiFetchAudit.fetched_at.desc())
        .limit(limit)
        .all()
    )

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


@app.get("/health", response_model=HealthResponse, include_in_schema=False)
def health():
    # A simple liveness check — returns 200 with "healthy" if the server is running.
    # include_in_schema=False hides it from the /docs page (it's internal, not for users).
    # Useful for load balancers or monitoring tools that ping this to check if the app is up.
    return HealthResponse(status="healthy", timestamp=datetime.now(timezone.utc))
