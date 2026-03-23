# etl.py
# ETL stands for Extract, Transform, Load - the three steps of a data pipeline:
#   Extract  = fetch raw data from the SAM.gov API
#   Transform = pull out the specific fields we care about and clean them up
#   Load     = insert the cleaned data into our PostgreSQL database
#
# This file replaces both Program.cs and DatabaseManager.cs from the C# version.
# Run it directly from the terminal:  python etl.py

import json
import sys
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Union

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

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
    # Returns the (posted_from, posted_to) date strings we send to the API
    # If you set SAM_POSTED_FROM and SAM_POSTED_TO in your .env file those are used
    # Otherwise we default to the last 7 days so you always get recent data
    if settings.sam_posted_from and settings.sam_posted_to:
        return settings.sam_posted_from.strip(), settings.sam_posted_to.strip()

    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)

    # SAM.gov requires dates in MM/dd/yyyy format exactly - other formats will fail
    fmt = "%m/%d/%Y"
    return week_ago.strftime(fmt), today.strftime(fmt)


def build_request(posted_from: str, posted_to: str) -> Tuple[str, Dict]:
    # Returns the base URL and a params dict separately
    # httpx will handle URL-encoding the params automatically (e.g. slashes in dates)
    # so we don't have to manually escape anything like we did in C#
    params = {
        "api_key":    settings.sam_api_key,  # pulled from .env via config.py
        "postedFrom": posted_from,
        "postedTo":   posted_to,
        "limit":      str(settings.sam_fetch_limit),
    }
    return settings.sam_api_base_url, params


def save_raw_data(db: Session, raw_json: Union[Dict, str], success: bool) -> None:
    # Always save the raw API response before we try to parse anything
    # If the JSON structure changes or parsing breaks, we can still look at this
    if isinstance(raw_json, str):
        # If we got a string back (e.g. the response wasn't valid JSON) wrap it
        try:
            raw_json = json.loads(raw_json)
        except json.JSONDecodeError:
            raw_json = {"raw_text": raw_json}

    row = RawApiData(
        source_name=   "SAM.gov",
        raw_json=      raw_json,
        status=        "Success" if success else "Failed",
        error_message= None if success else "API call failed",
    )
    db.add(row)
    db.commit()


def log_audit(db: Session, status_code: int, success: bool, posted_from: str, posted_to: str) -> None:
    # Write one audit row per ETL run so we have a history of when fetches happened
    # and whether they succeeded - visible via GET /applications in the API
    row = ApiFetchAudit(
        source_name= "SAM.gov",
        status_code= str(status_code),
        was_success= success,
        posted_from= posted_from,
        posted_to=   posted_to,
    )
    db.add(row)
    db.commit()


def log_error(db: Session, context: str, message: str) -> None:
    # Saves errors to the database instead of just printing them
    # context describes where the error happened, message is the actual error text
    row = ErrorLog(error_context=context, error_message=message)
    db.add(row)
    db.commit()
    print(f"[ERROR LOGGED] {context}: {message}")


def upsert_agency(db: Session, name: str) -> int:
    # "Upsert" means insert if new, skip if already exists
    # ON CONFLICT DO NOTHING means if this agency name is already in the table,
    # PostgreSQL ignores the insert instead of throwing a duplicate key error
    stmt = (
        pg_insert(Agency)
        .values(name=name)
        .on_conflict_do_nothing(index_elements=["name"])
    )
    db.execute(stmt)
    db.commit()

    # After the upsert we query back to get the id, whether it was just inserted
    # or was already there - we need this id as the foreign key on the contract
    agency = db.query(Agency).filter(Agency.name == name).one()
    return agency.id


def upsert_contract(
    db: Session,
    notice_id: str,
    title: str,
    sol_num: str,
    agency_id: int,
    posted_date: str,
) -> None:
    # ON CONFLICT DO UPDATE means if a contract with this notice_id already exists,
    # update all its fields with the latest data from the API instead of skipping
    # This keeps the database fresh if SAM.gov updates a contract's details
    stmt = (
        pg_insert(Contract)
        .values(
            notice_id=           notice_id,
            title=               title,
            solicitation_number= sol_num,
            agency_id=           agency_id,
            posted_date=         posted_date,
        )
        .on_conflict_do_update(
            index_elements=["notice_id"],
            set_={
                "title":               title,
                "solicitation_number": sol_num,
                "agency_id":           agency_id,
                "posted_date":         posted_date,
            },
        )
    )
    db.execute(stmt)
    db.commit()


def extract_and_load(db: Session, raw_json: dict) -> None:
    # This is the Transform + Load step
    # We walk through each opportunity in the JSON and map fields to our table columns
    opportunities = raw_json.get("opportunitiesData", [])

    if not opportunities:
        log_error(db, "JSON Parsing", "No opportunitiesData array found in the JSON payload.")
        return

    records_processed = 0

    for opp in opportunities:
        # Use .get() with fallbacks so a missing field doesn't crash the whole loop
        # If noticeId is missing we generate a random UUID so the row still has a unique key
        notice_id   = opp.get("noticeId")            or str(uuid.uuid4())
        title       = opp.get("title")               or "Untitled"
        sol_num     = opp.get("solicitationNumber")  or "N/A"
        posted_date = opp.get("postedDate")          or "Unknown Date"

        # SAM.gov sometimes uses "department" and sometimes uses "agency" for the same field
        # We check both and fall back to a default if neither is present
        agency_name = opp.get("department") or opp.get("agency") or "Unknown Agency"

        # Insert the agency first (we need its id for the contract foreign key)
        agency_id = upsert_agency(db, agency_name)

        # Now insert the contract linked to that agency
        upsert_contract(db, notice_id, title, sol_num, agency_id, posted_date)
        records_processed += 1

    print(f"Parsed and inserted {records_processed} cleaned record(s).")


def print_summary(db: Session) -> None:
    # Quick sanity check - prints row counts so you can confirm data actually got loaded
    raw_count      = db.query(RawApiData).count()
    contract_count = db.query(Contract).count()

    print("\n--- DATABASE SUMMARY ---")
    print(f"Total raw JSON records : {raw_count}")
    print(f"Total contract records : {contract_count}")
    print("------------------------\n")


def run_etl() -> None:
    # Check the API key before doing anything else - no point hitting the network
    # if we know the request will be rejected
    if not settings.sam_api_key or settings.sam_api_key == "YOUR_API_KEY_HERE":
        print("API key is required. Set SAM_API_KEY in your .env file.")
        sys.exit(1)

    # Make sure all the tables exist before we try to write to them
    # If you already have the C# database this will just verify and move on
    init_db()

    posted_from, posted_to = get_date_range()
    base_url, params = build_request(posted_from, posted_to)

    print(f"Fetching SAM.gov data posted between {posted_from} and {posted_to}...")

    # Open one database session for the entire ETL run
    db = SessionLocal()

    try:
        # httpx.get sends the HTTP request - timeout=30 means give up after 30 seconds
        response = httpx.get(base_url, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        # Try to parse the response as JSON - if it's malformed wrap it in a dict
        try:
            raw_json = response.json()
        except Exception:
            raw_json = {"raw_text": response.text}

        # Always save raw data and audit log regardless of success or failure
        save_raw_data(db, raw_json, response.is_success)
        log_audit(db, response.status_code, response.is_success, posted_from, posted_to)

        if response.is_success:
            extract_and_load(db, raw_json)
        else:
            # Log the failure but don't crash - we already saved the raw response
            log_error(
                db,
                "API Fetch Failed",
                f"Non-success status {response.status_code}: {response.text[:500]}",
            )

        print_summary(db)

    except httpx.RequestError as exc:
        # RequestError covers network-level failures like timeouts or DNS errors
        print(f"Network error: {exc}")
        log_error(db, "Network Error", str(exc))

    except Exception as exc:
        # Catch anything else unexpected so the process exits cleanly
        print(f"Unexpected error: {exc}")
        log_error(db, "Unexpected Error", str(exc))

    finally:
        # Always close the session even if an exception occurred above
        db.close()


# Only runs when you execute this file directly: python etl.py
# If another file imports etl.py, this block is skipped
if __name__ == "__main__":
    run_etl()