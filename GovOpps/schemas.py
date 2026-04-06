# schemas.py
# Pydantic models that define the exact shape of our API responses.
#
# Pydantic is a data validation library. These classes tell FastAPI:
#   1. What fields each API response must have
#   2. What type each field must be
#   3. Which fields are optional vs required
#
# FastAPI uses these automatically to:
#   - Validate data before sending it (so you never return broken JSON)
#   - Generate the interactive /docs page with correct field types shown

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    # A base class shared by all our response models.
    # from_attributes=True tells Pydantic: "it's okay to build this model
    # directly from a SQLAlchemy row object, not just from a plain dict."
    # Without this, you'd have to manually convert every DB row to a dict
    # before Pydantic could read it.
    model_config = ConfigDict(from_attributes=True)


class ContractResponse(ORMBase):
    # The shape of a single contract in the GET /contracts response.
    # Optional[str] means the field can be a string OR None (null in JSON).
    contract_id:         int
    notice_id:           Optional[str]   # SAM.gov's unique ID — may be missing for old rows
    title:               Optional[str]   # the contract title
    solicitation_number: Optional[str]   # government reference number
    agency_id:           Optional[int]   # foreign key to the agency table
    agency_name:         str             # not Optional — we always join to get this
    posted_date:         Optional[str]   # when the opportunity was posted on SAM.gov


class VendorResponse(ORMBase):
    # The shape of a single agency entry in the GET /vendors response.
    # Includes a computed count of how many contracts that agency has posted.
    agency_id:      int
    agency_name:    str
    contract_count: int  # calculated with COUNT() in the SQL query, not stored in the DB


class ApplicationResponse(ORMBase):
    # The shape of a single ETL run record in the GET /applications response.
    # "Applications" here means ETL pipeline runs, not job applications.
    id:          int
    source_name: str      # always "SAM.gov"
    status_code: str      # HTTP status code, e.g. "200"
    was_success: bool     # True = the fetch worked, False = it failed
    posted_from: str      # the start date we requested from SAM.gov
    posted_to:   str      # the end date we requested from SAM.gov
    fetched_at:  datetime # timestamp of when this ETL run happened


class HealthResponse(BaseModel):
    # Simple response for the GET /health endpoint — used to check if the API is alive.
    # Does NOT inherit ORMBase because it's never built from a database row.
    status:    str       # always "healthy" if the server is running
    timestamp: datetime  # current server time, useful for confirming the response is fresh
