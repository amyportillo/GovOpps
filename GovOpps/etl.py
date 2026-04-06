# etl.py
# ETL pipeline — Extract, Transform, Load.
#   Extract  = fetch raw contract data from the SAM.gov API
#   Transform = pull out the fields we care about and clean them up
#   Load      = insert or update the cleaned records in PostgreSQL
#
# Run with: python run.py etl

import json
import sys
import uuid
from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict, Union

import httpx  # like the requests library but more modern — used to make HTTP calls
from sqlalchemy.orm import Session

from config import settings
from database import (
    SessionLocal,
    init_db,
    Agency,
    Contract,
    RawApiData,
    ApiFetchAudit,
    ErrorLog,
)


def get_date_range() -> Tuple[str, str]:
    # Determines the date range to fetch contracts for.
    # If the user set SAM_POSTED_FROM and SAM_POSTED_TO in .env, use those.
    # Otherwise, default to the last 7 days so we always get fresh data.
    if settings.sam_posted_from and settings.sam_posted_to:
        return settings.sam_posted_from.strip(), settings.sam_posted_to.strip()

    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)

    # SAM.gov requires MM/dd/yyyy format — other formats are rejected with an error.
    fmt = "%m/%d/%Y"
    return week_ago.strftime(fmt), today.strftime(fmt)


def build_request(posted_from: str, posted_to: str) -> Tuple[str, Dict]:
    # Assembles the URL and query parameters for the SAM.gov API call.
    # The API key is passed as a query param (not a header) — SAM.gov's requirement.
    params = {
        "api_key":    settings.sam_api_key,
        "postedFrom": posted_from,
        "postedTo":   posted_to,
        "limit":      str(settings.sam_fetch_limit),  # how many results to return (max 1000)
    }
    return settings.sam_api_base_url, params


def save_raw_data(db: Session, raw_json: Union[Dict, str], success: bool) -> None:
    # Saves the raw API response to the database BEFORE we try to parse it.
    # This is a safety net — if our parsing logic breaks or the data format changes,
    # we can still look back at exactly what SAM.gov sent us.
    if isinstance(raw_json, str):
        # If the response wasn't valid JSON (e.g. an HTML error page), wrap it in a dict
        # so we can still store it in the JSONB column without crashing.
        try:
            raw_json = json.loads(raw_json)
        except json.JSONDecodeError:
            raw_json = {"raw_text": raw_json}

    db.add(RawApiData(
        source_name=   "SAM.gov",
        raw_json=      raw_json,
        status=        "Success" if success else "Failed",
        error_message= None if success else "API call failed",
    ))
    db.commit()


def log_audit(db: Session, status_code: int, success: bool, posted_from: str, posted_to: str) -> None:
    # Records a single ETL run in the audit log — one row per run.
    # This is how the dashboard knows the run history and success rate.
    db.add(ApiFetchAudit(
        source_name= "SAM.gov",
        status_code= str(status_code),
        was_success= success,
        posted_from= posted_from,
        posted_to=   posted_to,
    ))
    db.commit()


def log_error(db: Session, context: str, message: str) -> None:
    # Writes an error to the error_log table and also prints it to the terminal.
    # context describes WHERE the error happened (e.g. "API Fetch", "JSON Parsing").
    # message is the actual error text.
    db.add(ErrorLog(error_context=context, error_message=message))
    db.commit()
    print(f"[ERROR] {context}: {message}")


def extract_and_load(db: Session, raw_json: dict) -> None:
    # The core of the ETL — parses each contract from the API response
    # and inserts new ones or updates existing ones in the database.

    # SAM.gov returns contracts in a key called "opportunitiesData"
    opportunities = raw_json.get("opportunitiesData", [])

    if not opportunities:
        log_error(db, "JSON Parsing", "No opportunitiesData found in the response.")
        return

    # Load ALL existing agencies into a dict once — key: name, value: id.
    # This avoids hitting the database on every single contract to check if an agency exists.
    # With 1000 contracts, that's 1000 queries saved.
    agency_cache: dict = {a.agency_name: a.agency_id for a in db.query(Agency).all()}

    # Load ALL existing notice_ids into a set — used to detect duplicates.
    # Set lookups are O(1) (instant), vs a DB query per contract which would be very slow.
    existing_notice_ids: set = {c.notice_id for c in db.query(Contract.notice_id).all()}

    new_contracts    = []  # contracts we haven't seen before — will be bulk inserted
    update_contracts = []  # contracts we already have — will be updated in place

    for opp in opportunities:
        # Pull out the fields we care about, with safe fallbacks if any are missing.
        notice_id   = opp.get("noticeId")           or str(uuid.uuid4())  # generate an ID if missing
        title       = opp.get("title")              or "Untitled"
        sol_num     = opp.get("solicitationNumber") or "N/A"
        posted_date = opp.get("postedDate")         or "Unknown Date"

        # fullParentPathName is a dot-separated hierarchy of org names, like:
        # "DEPT OF DEFENSE.DEFENSE LOGISTICS AGENCY.DLA MARITIME - PUGET SOUND"
        # We split on "." and take just the first segment as the top-level agency name.
        full_path   = opp.get("fullParentPathName") or ""
        agency_name = full_path.split(".")[0].strip() if full_path else "Unknown Agency"

        # If this agency doesn't exist yet (not in DB and not in this batch), create it.
        # db.flush() sends the INSERT to Postgres immediately so we can get the new agency_id,
        # but doesn't commit — the whole thing is still part of the current transaction.
        if agency_name not in agency_cache:
            new_agency = Agency(agency_name=agency_name)
            db.add(new_agency)
            db.flush()  # get the auto-generated agency_id without a full commit
            agency_cache[agency_name] = new_agency.agency_id

        agency_id = agency_cache[agency_name]

        # If we've already stored this contract, queue it for an update.
        # Otherwise, add it to the new batch.
        if notice_id in existing_notice_ids:
            update_contracts.append({
                "notice_id": notice_id, "title": title,
                "solicitation_number": sol_num, "agency_id": agency_id, "posted_date": posted_date,
            })
        else:
            new_contracts.append(Contract(
                notice_id=notice_id, title=title,
                solicitation_number=sol_num, agency_id=agency_id, posted_date=posted_date,
            ))
            # Add to the set so duplicates within this same batch are also caught
            existing_notice_ids.add(notice_id)

    # Bulk insert all new contracts in a single DB call — much faster than inserting one by one.
    if new_contracts:
        db.bulk_save_objects(new_contracts)

    # Update any contracts that already existed in the DB
    for u in update_contracts:
        db.query(Contract).filter(Contract.notice_id == u["notice_id"]).update({
            "title": u["title"], "solicitation_number": u["solicitation_number"],
            "agency_id": u["agency_id"], "posted_date": u["posted_date"],
        })

    # One single commit saves all inserts and updates together atomically.
    # If anything fails, the whole batch rolls back — no partial saves.
    db.commit()
    print(f"Loaded {len(new_contracts)} new + {len(update_contracts)} updated contract(s).")


def trim_contracts(db: Session, max_contracts: int = 1000) -> None:
    # Keeps the contract table from growing forever.
    # If we have more than max_contracts rows, delete the oldest ones.
    # "Oldest" is determined by posted_date, then contract_id as a tiebreaker.
    total = db.query(Contract).count()
    if total <= max_contracts:
        return  # already within limit, nothing to do

    # Find the contract_id of the Nth newest record (the cutoff point).
    # Any contract with an ID at or below this cutoff is considered "old" and gets deleted.
    cutoff = (
        db.query(Contract.contract_id)
        .order_by(Contract.posted_date.desc(), Contract.contract_id.desc())
        .offset(max_contracts)  # skip the top max_contracts rows
        .limit(1)
        .scalar()               # .scalar() returns a single value instead of a list
    )

    if cutoff:
        deleted = (
            db.query(Contract)
            .filter(Contract.contract_id <= cutoff)
            .delete(synchronize_session=False)  # skip updating SQLAlchemy's in-memory state (faster)
        )
        db.commit()
        print(f"Trimmed {deleted} old contract(s) to stay at {max_contracts} limit.")


def print_summary(db: Session) -> None:
    # Prints a quick summary to the terminal after the ETL finishes.
    raw_count      = db.query(RawApiData).count()
    contract_count = db.query(Contract).count()

    print("\n--- Summary ---")
    print(f"Raw API records : {raw_count}")
    print(f"Contracts       : {contract_count}")
    print("---------------\n")


def run_etl() -> None:
    # The main function — orchestrates the entire ETL from top to bottom.
    # Called by run.py when you run: python run.py etl

    # Refuse to run if the API key is still the default placeholder
    if not settings.sam_api_key or settings.sam_api_key == "YOUR_API_KEY_HERE":
        print("Set SAM_API_KEY in your .env file before running.")
        sys.exit(1)

    # Make sure the DB columns exist before we try to use them
    init_db()

    posted_from, posted_to = get_date_range()
    base_url, params = build_request(posted_from, posted_to)

    print(f"Fetching contracts posted {posted_from} → {posted_to}...")

    # Open a database session manually here (not via Depends) because this is a
    # script, not an HTTP request — FastAPI's dependency injection doesn't apply.
    db = SessionLocal()
    try:
        # Make the HTTP request to SAM.gov with a 30-second timeout
        response = httpx.get(base_url, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        # Try to parse the response as JSON. If it's not valid JSON (e.g. an error HTML page),
        # wrap the raw text in a dict so we can still save it to the DB.
        try:
            raw_json = response.json()
        except Exception:
            raw_json = {"raw_text": response.text}

        # Always save the raw response and log the audit record, regardless of success or failure
        save_raw_data(db, raw_json, response.is_success)
        log_audit(db, response.status_code, response.is_success, posted_from, posted_to)

        if response.is_success:
            # Parse contracts out of the JSON and save them to the DB
            extract_and_load(db, raw_json)
            # Delete old contracts to keep the table at 1000 rows max
            trim_contracts(db, max_contracts=1000)
        else:
            # Log the failure — the first 500 chars of the response body is usually enough context
            log_error(db, "API Fetch", f"Status {response.status_code}: {response.text[:500]}")

        print_summary(db)

    except httpx.RequestError as exc:
        # This catches network-level errors: DNS failure, connection refused, timeout, etc.
        print(f"Network error: {exc}")
        log_error(db, "Network Error", str(exc))

    except Exception as exc:
        # Catch-all for anything unexpected — parsing errors, DB errors, etc.
        print(f"Unexpected error: {exc}")
        log_error(db, "Unexpected Error", str(exc))

    finally:
        # Always close the DB session even if we crashed halfway through
        db.close()


if __name__ == "__main__":
    # Allows running this file directly: python etl.py
    # Normally you'd use: python run.py etl
    run_etl()
