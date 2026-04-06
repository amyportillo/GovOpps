# etl.py
# ETL pipeline — Extract, Transform, Load.
#   Extract  = fetch raw contract data from the SAM.gov API
#   Transform = pull out the fields we care about
#   Load      = insert cleaned records into PostgreSQL
#
# Run with: python run.py etl

import json
import sys
import uuid
from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict, Union

import httpx
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
    # Use custom dates from .env if set, otherwise default to the last 7 days
    if settings.sam_posted_from and settings.sam_posted_to:
        return settings.sam_posted_from.strip(), settings.sam_posted_to.strip()

    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)

    # SAM.gov requires MM/dd/yyyy — other formats get rejected
    fmt = "%m/%d/%Y"
    return week_ago.strftime(fmt), today.strftime(fmt)


def build_request(posted_from: str, posted_to: str) -> Tuple[str, Dict]:
    params = {
        "api_key":    settings.sam_api_key,
        "postedFrom": posted_from,
        "postedTo":   posted_to,
        "limit":      str(settings.sam_fetch_limit),
    }
    return settings.sam_api_base_url, params


def save_raw_data(db: Session, raw_json: Union[Dict, str], success: bool) -> None:
    # Save the raw API response before parsing anything
    # If parsing breaks later, we can always come back to this
    if isinstance(raw_json, str):
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
    db.add(ApiFetchAudit(
        source_name= "SAM.gov",
        status_code= str(status_code),
        was_success= success,
        posted_from= posted_from,
        posted_to=   posted_to,
    ))
    db.commit()


def log_error(db: Session, context: str, message: str) -> None:
    db.add(ErrorLog(error_context=context, error_message=message))
    db.commit()
    print(f"[ERROR] {context}: {message}")


def extract_and_load(db: Session, raw_json: dict) -> None:
    opportunities = raw_json.get("opportunitiesData", [])

    if not opportunities:
        log_error(db, "JSON Parsing", "No opportunitiesData found in the response.")
        return

    # Load all existing agencies into memory once — avoids one DB query per contract
    agency_cache: dict = {a.agency_name: a.agency_id for a in db.query(Agency).all()}

    # Load all existing notice_ids into a set — O(1) lookup instead of one query per contract
    existing_notice_ids: set = {c.notice_id for c in db.query(Contract.notice_id).all()}

    new_agencies  = []
    new_contracts = []
    update_contracts = []

    for opp in opportunities:
        notice_id   = opp.get("noticeId")           or str(uuid.uuid4())
        title       = opp.get("title")              or "Untitled"
        sol_num     = opp.get("solicitationNumber") or "N/A"
        posted_date = opp.get("postedDate")         or "Unknown Date"
        # fullParentPathName is a dot-separated hierarchy like:
        # "DEPT OF DEFENSE.DEFENSE LOGISTICS AGENCY.DLA MARITIME..."
        # We take the first segment as the top-level department name
        full_path   = opp.get("fullParentPathName") or ""
        agency_name = full_path.split(".")[0].strip() if full_path else "Unknown Agency"

        # Create the agency if we haven't seen it yet (in DB or in this batch)
        if agency_name not in agency_cache:
            new_agency = Agency(agency_name=agency_name)
            db.add(new_agency)
            db.flush()  # gets the new id without a full commit
            agency_cache[agency_name] = new_agency.agency_id

        agency_id = agency_cache[agency_name]

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
            existing_notice_ids.add(notice_id)

    # Bulk insert new contracts in one shot
    if new_contracts:
        db.bulk_save_objects(new_contracts)

    # Update existing contracts
    for u in update_contracts:
        db.query(Contract).filter(Contract.notice_id == u["notice_id"]).update({
            "title": u["title"], "solicitation_number": u["solicitation_number"],
            "agency_id": u["agency_id"], "posted_date": u["posted_date"],
        })

    # One commit for everything
    db.commit()
    print(f"Loaded {len(new_contracts)} new + {len(update_contracts)} updated contract(s).")


def trim_contracts(db: Session, max_contracts: int = 1000) -> None:
    # Keep only the newest max_contracts records by posted_date.
    # Any contract beyond that limit (oldest ones) gets deleted.
    total = db.query(Contract).count()
    if total <= max_contracts:
        return

    # Find the cutoff — the contract_id of the Nth newest record
    cutoff = (
        db.query(Contract.contract_id)
        .order_by(Contract.posted_date.desc(), Contract.contract_id.desc())
        .offset(max_contracts)
        .limit(1)
        .scalar()
    )

    if cutoff:
        deleted = (
            db.query(Contract)
            .filter(Contract.contract_id <= cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        print(f"Trimmed {deleted} old contract(s) to stay at {max_contracts} limit.")


def print_summary(db: Session) -> None:
    raw_count      = db.query(RawApiData).count()
    contract_count = db.query(Contract).count()

    print("\n--- Summary ---")
    print(f"Raw API records : {raw_count}")
    print(f"Contracts       : {contract_count}")
    print("---------------\n")


def run_etl() -> None:
    if not settings.sam_api_key or settings.sam_api_key == "YOUR_API_KEY_HERE":
        print("Set SAM_API_KEY in your .env file before running.")
        sys.exit(1)

    init_db()

    posted_from, posted_to = get_date_range()
    base_url, params = build_request(posted_from, posted_to)

    print(f"Fetching contracts posted {posted_from} → {posted_to}...")

    db = SessionLocal()
    try:
        response = httpx.get(base_url, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        try:
            raw_json = response.json()
        except Exception:
            raw_json = {"raw_text": response.text}

        save_raw_data(db, raw_json, response.is_success)
        log_audit(db, response.status_code, response.is_success, posted_from, posted_to)

        if response.is_success:
            extract_and_load(db, raw_json)
            trim_contracts(db, max_contracts=1000)
        else:
            log_error(db, "API Fetch", f"Status {response.status_code}: {response.text[:500]}")

        print_summary(db)

    except httpx.RequestError as exc:
        print(f"Network error: {exc}")
        log_error(db, "Network Error", str(exc))

    except Exception as exc:
        print(f"Unexpected error: {exc}")
        log_error(db, "Unexpected Error", str(exc))

    finally:
        db.close()


if __name__ == "__main__":
    run_etl()
