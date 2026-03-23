# schemas.py
# Pydantic models that define exactly what shape our API responses will have.
# FastAPI reads these and automatically:
#   - Validates that every field has the right type before sending a response
#   - Generates the Swagger documentation at /docs so you can see all fields
#   - Serializes Python objects (like SQLAlchemy rows) into JSON automatically
#
# Think of these like the DTO classes from the C# version (ContractDto, VendorDto, etc.)

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# All our response models inherit from this base class
# from_attributes=True tells Pydantic it's allowed to read values off
# SQLAlchemy ORM objects (which use attribute access) instead of just dicts
class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Shape of one item returned by GET /contracts
class ContractResponse(ORMBase):
    id:                  int
    notice_id:           str
    title:               Optional[str]       # Optional[str] means the field can be null
    solicitation_number: Optional[str]
    agency_id:           int
    agency_name:         str                 # joined from the agency table, not stored on contract
    posted_date:         Optional[str]
    created_at:          datetime


# Shape of one item returned by GET /vendors
class VendorResponse(ORMBase):
    id:             int
    name:           str
    contract_count: int                      # calculated with COUNT() in the query
    created_at:     datetime


# Shape of one item returned by GET /applications
# Each row here represents one run of the etl.py script
class ApplicationResponse(ORMBase):
    id:          int
    source_name: str
    status_code: str
    was_success: bool
    posted_from: str
    posted_to:   str
    fetched_at:  datetime


# Shape returned by GET /health - just a quick status check
class HealthResponse(BaseModel):
    status:    str
    timestamp: datetime