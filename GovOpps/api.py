# api.py
# FastAPI app with all three endpoints.
# Auto-generated docs available at http://localhost:8000/docs
#
# Start with: python run.py api

from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db, init_db, Agency, Contract, ApiFetchAudit
from schemas import ContractResponse, VendorResponse, ApplicationResponse, HealthResponse


app = FastAPI(
    title="Gov Contracts API",
    version="1.0.0",
    description="Government contract opportunities from SAM.gov. Run `python run.py etl` first to load data.",
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/contracts", response_model=list[ContractResponse], tags=["Contracts"])
def get_contracts(
    limit:     int           = Query(default=100, ge=1, le=1000, description="Max rows to return"),
    agency_id: Optional[int] = Query(default=None, description="Filter by agency ID"),
    db:        Session       = Depends(get_db),
):
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

    if agency_id is not None:
        query = query.filter(Contract.agency_id == agency_id)

    rows = query.order_by(Contract.contract_id.desc()).limit(limit).all()

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
    search: Optional[str] = Query(default=None, description="Filter by agency name (case-insensitive)"),
    db:     Session       = Depends(get_db),
):
    query = (
        db.query(
            Agency.agency_id,
            Agency.agency_name,
            func.count(Contract.contract_id).label("contract_count"),
        )
        .outerjoin(Contract, Contract.agency_id == Agency.agency_id)
        .group_by(Agency.agency_id, Agency.agency_name)
    )

    if search:
        query = query.filter(Agency.agency_name.ilike(f"%{search}%"))

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
    return HealthResponse(status="healthy", timestamp=datetime.now(timezone.utc))
