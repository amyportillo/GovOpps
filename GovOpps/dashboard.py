# dashboard.py
# FastAPI app that serves the visual dashboard on port 8501.
# Unlike api.py which returns JSON, every route here returns a full HTML page.
#
# Start with: python run.py dashboard  open http://localhost:8501

from fastapi import FastAPI
from fastapi.responses import HTMLResponse  # tells FastAPI to send HTML instead of JSON
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
    # Queries that are needed on EVERY page — the "last sync" time and pipeline status
    # shown in the sidebar footer. Factored out here so we don't repeat it in every route.
    last_run   = db.query(ApiFetchAudit).order_by(ApiFetchAudit.fetched_at.desc()).first()
    total_runs = db.query(ApiFetchAudit).count()
    return {
        # Format the timestamp nicely, e.g. "Apr 05 10:32 PM". Falls back to "never" if no runs yet.
        "last_sync":       last_run.fetched_at.strftime("%b %d %I:%M %p") if last_run else "never",
        "pipeline_status": "running" if total_runs > 0 else "no runs yet",
    }


def page(active, title, content, ctx):
    # Wraps any page's content in the full HTML shell (sidebar + topbar).
    # active  = the page ID to highlight in the sidebar (e.g. "contracts")
    # title   = the text shown in the topbar and browser tab
    # content = the inner HTML from one of the pages.py functions
    # ctx     = the shared data dict (last_sync, pipeline_status)
    return layout(active, title, content, ctx["last_sync"], ctx["pipeline_status"])


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard():
    # The main dashboard page — shows summary metrics, charts, and recent contracts.
    db = SessionLocal()
    try:
        ctx = shared(db)  # get sidebar data shared across all pages

        # Fetch all ETL run records to compute total runs and success rate
        all_runs    = db.query(ApiFetchAudit).all()
        etl_runs    = len(all_runs)
        success_cnt = sum(1 for r in all_runs if r.was_success)

        # Top 6 agencies by number of contracts — used for the bar chart
        agency_rows = (
            db.query(Agency.agency_name, func.count(Contract.contract_id).label("count"))
            .join(Contract, Contract.agency_id == Agency.agency_id)
            .group_by(Agency.agency_name)
            .order_by(func.count(Contract.contract_id).desc())
            .limit(6).all()
        )

        # Last 6 ETL runs for the "Recent ETL runs" mini log card
        recent_runs = db.query(ApiFetchAudit).order_by(ApiFetchAudit.fetched_at.desc()).limit(6).all()

        # Most recent 50 contracts for the table at the bottom of the dashboard
        contract_rows = (
            db.query(Contract.notice_id, Contract.title, Agency.agency_name, Contract.posted_date)
            .join(Agency, Agency.agency_id == Contract.agency_id)
            .order_by(Contract.posted_date.desc(), Contract.contract_id.desc()).limit(50).all()
        )

        # Raw SQL for the daily trend chart — groups contracts by date and counts them.
        # We use raw SQL here because SQLAlchemy's ORM makes GROUP BY on a text column awkward.
        daily_rows = db.execute(text("""
            SELECT posted_date, COUNT(*) as count
            FROM contract
            WHERE posted_date IS NOT NULL
            GROUP BY posted_date
            ORDER BY posted_date ASC
            LIMIT 30
        """)).fetchall()

        # Bundle everything into a single dict the template function will consume
        data = {
            **ctx,  # spread in the shared sidebar data
            "total_contracts": db.query(Contract).count(),
            "total_agencies":  db.query(Agency).count(),
            "etl_runs":        etl_runs,
            # Compute success rate as a percentage string, e.g. "95%". Shows "—" if no runs yet.
            "success_rate":    f"{int(success_cnt / etl_runs * 100)}%" if etl_runs else "—",
            "error_count":     db.query(ErrorLog).count(),
            "agency_data":     [{"name": r.agency_name, "count": r.count} for r in agency_rows],
            "etl_log":         [{"time": r.fetched_at.strftime("%b %d %I:%M %p"), "source": r.source_name, "success": r.was_success} for r in recent_runs],
            "contracts":       [{"notice_id": r.notice_id, "title": r.title, "agency": r.agency_name, "posted_date": r.posted_date} for r in contract_rows],
            "daily_trend":     [{"date": r[0], "count": r[1]} for r in daily_rows],
        }

        # dashboard_page() turns the data dict into inner HTML, then page() wraps it in the layout
        return page("dashboard", "Dashboard", dashboard_page(data), ctx)
    finally:
        db.close()  # always close the session, even if a query crashes


@app.get("/contracts", response_class=HTMLResponse)
def contracts():
    # Full contracts table — all contracts with a live search box.
    db = SessionLocal()
    try:
        ctx = shared(db)
        rows = (
            db.query(Contract.notice_id, Contract.title, Agency.agency_name, Contract.solicitation_number, Contract.posted_date)
            .join(Agency, Agency.agency_id == Contract.agency_id)
            .order_by(Contract.posted_date.desc(), Contract.contract_id.desc()).all()
        )
        # Convert SQLAlchemy row objects into plain dicts for the template
        data = [{"notice_id": r.notice_id, "title": r.title, "agency": r.agency_name, "sol_num": r.solicitation_number, "posted_date": r.posted_date} for r in rows]
        return page("contracts", "Contracts", contracts_page(data, len(data)), ctx)
    finally:
        db.close()


@app.get("/vendors", response_class=HTMLResponse)
def vendors():
    # Agencies ranked by number of contracts — shown as cards and a searchable table.
    db = SessionLocal()
    try:
        ctx = shared(db)
        rows = (
            db.query(Agency.agency_name, func.count(Contract.contract_id).label("count"))
            .outerjoin(Contract, Contract.agency_id == Agency.agency_id)  # outerjoin = include agencies with 0 contracts
            .group_by(Agency.agency_name)
            .order_by(func.count(Contract.contract_id).desc()).all()
        )
        data = [{"name": r.agency_name, "count": r.count} for r in rows]
        return page("vendors", "Vendors", vendors_page(data), ctx)
    finally:
        db.close()


@app.get("/applications", response_class=HTMLResponse)
def applications():
    # Full ETL run history — every fetch attempt with its result and date range.
    # "Applications" here means ETL pipeline runs, not job applications.
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
    # Error log page — shows all errors recorded during ETL runs.
    # If this page is empty, everything has been running cleanly.
    db = SessionLocal()
    try:
        ctx = shared(db)
        rows = db.query(ErrorLog).order_by(ErrorLog.logged_at.desc()).all()
        data = [
            {
                "time":    r.logged_at.strftime("%b %d %Y %I:%M %p"),
                "context": r.error_context,  # where the error happened (e.g. "API Fetch")
                "message": r.error_message,  # what went wrong
            }
            for r in rows
        ]
        return page("errors", "Error Log", errors_page(data), ctx)
    finally:
        db.close()
