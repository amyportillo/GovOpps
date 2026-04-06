# dashboard.py
# FastAPI app that serves the dashboard UI on port 8501.
# Each route loads data and returns a full HTML page.
#
# Start with: python run.py dashboard  →  open http://localhost:8501

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sqlalchemy import func, text

from database import SessionLocal, Agency, Contract, ApiFetchAudit, ErrorLog
from templates.components import layout
from templates.pages import (
    dashboard_page,
    contracts_page,
    vendors_page,
    applications_page,
    errors_page,
)

app = FastAPI()


def shared(db) -> dict:
    # Values shown on every page (sidebar footer + pipeline badge)
    last_run = db.query(ApiFetchAudit).order_by(ApiFetchAudit.fetched_at.desc()).first()
    total_runs  = db.query(ApiFetchAudit).count()
    return {
        "last_sync":       last_run.fetched_at.strftime("%b %d %I:%M %p") if last_run else "never",
        "pipeline_status": "running" if total_runs > 0 else "no runs yet",
    }


def page(active, title, content, ctx):
    return layout(active, title, content, ctx["last_sync"], ctx["pipeline_status"])


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard():
    db = SessionLocal()
    try:
        ctx = shared(db)

        all_runs    = db.query(ApiFetchAudit).all()
        etl_runs    = len(all_runs)
        success_cnt = sum(1 for r in all_runs if r.was_success)

        agency_rows = (
            db.query(Agency.agency_name, func.count(Contract.contract_id).label("count"))
            .join(Contract, Contract.agency_id == Agency.agency_id)
            .group_by(Agency.agency_name)
            .order_by(func.count(Contract.contract_id).desc())
            .limit(6).all()
        )

        recent_runs = db.query(ApiFetchAudit).order_by(ApiFetchAudit.fetched_at.desc()).limit(6).all()

        contract_rows = (
            db.query(Contract.notice_id, Contract.title, Agency.agency_name, Contract.posted_date)
            .join(Agency, Agency.agency_id == Contract.agency_id)
            .order_by(Contract.posted_date.desc(), Contract.contract_id.desc()).limit(50).all()
        )

        daily_rows = db.execute(text("""
            SELECT posted_date, COUNT(*) as count
            FROM contract
            WHERE posted_date IS NOT NULL
            GROUP BY posted_date
            ORDER BY posted_date ASC
            LIMIT 30
        """)).fetchall()

        data = {
            **ctx,
            "total_contracts": db.query(Contract).count(),
            "total_agencies":  db.query(Agency).count(),
            "etl_runs":        etl_runs,
            "success_rate":    f"{int(success_cnt / etl_runs * 100)}%" if etl_runs else "—",
            "error_count":     db.query(ErrorLog).count(),
            "agency_data":     [{"name": r.agency_name, "count": r.count} for r in agency_rows],
            "etl_log":         [{"time": r.fetched_at.strftime("%b %d %I:%M %p"), "source": r.source_name, "success": r.was_success} for r in recent_runs],
            "contracts":       [{"notice_id": r.notice_id, "title": r.title, "agency": r.agency_name, "posted_date": r.posted_date} for r in contract_rows],
            "daily_trend":     [{"date": r[0], "count": r[1]} for r in daily_rows],
        }

        return page("dashboard", "Dashboard", dashboard_page(data), ctx)
    finally:
        db.close()


@app.get("/contracts", response_class=HTMLResponse)
def contracts():
    db = SessionLocal()
    try:
        ctx = shared(db)
        rows = (
            db.query(Contract.notice_id, Contract.title, Agency.agency_name, Contract.solicitation_number, Contract.posted_date)
            .join(Agency, Agency.agency_id == Contract.agency_id)
            .order_by(Contract.posted_date.desc(), Contract.contract_id.desc()).all()
        )
        data = [{"notice_id": r.notice_id, "title": r.title, "agency": r.agency_name, "sol_num": r.solicitation_number, "posted_date": r.posted_date} for r in rows]
        return page("contracts", "Contracts", contracts_page(data, len(data)), ctx)
    finally:
        db.close()


@app.get("/vendors", response_class=HTMLResponse)
def vendors():
    db = SessionLocal()
    try:
        ctx = shared(db)
        rows = (
            db.query(Agency.agency_name, func.count(Contract.contract_id).label("count"))
            .outerjoin(Contract, Contract.agency_id == Agency.agency_id)
            .group_by(Agency.agency_name)
            .order_by(func.count(Contract.contract_id).desc()).all()
        )
        data = [{"name": r.agency_name, "count": r.count} for r in rows]
        return page("vendors", "Vendors", vendors_page(data), ctx)
    finally:
        db.close()


@app.get("/applications", response_class=HTMLResponse)
def applications():
    db = SessionLocal()
    try:
        ctx = shared(db)
        rows = db.query(ApiFetchAudit).order_by(ApiFetchAudit.fetched_at.desc()).all()
        data = [
            {
                "time":        r.fetched_at.strftime("%b %d %Y %I:%M %p"),
                "source":      r.source_name,
                "posted_from": r.posted_from,
                "posted_to":   r.posted_to,
                "status_code": r.status_code,
                "success":     r.was_success,
            }
            for r in rows
        ]
        return page("applications", "Applications", applications_page(data), ctx)
    finally:
        db.close()


@app.get("/errors", response_class=HTMLResponse)
def errors():
    db = SessionLocal()
    try:
        ctx = shared(db)
        rows = db.query(ErrorLog).order_by(ErrorLog.logged_at.desc()).all()
        data = [
            {
                "time":    r.logged_at.strftime("%b %d %Y %I:%M %p"),
                "context": r.error_context,
                "message": r.error_message,
            }
            for r in rows
        ]
        return page("errors", "Error Log", errors_page(data), ctx)
    finally:
        db.close()
