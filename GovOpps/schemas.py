# schemas.py
# Pydantic models that define the shape of our API responses.
# FastAPI uses these to validate responses and auto-generate the /docs page.

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ContractResponse(ORMBase):
    contract_id:         int
    notice_id:           Optional[str]
    title:               Optional[str]
    solicitation_number: Optional[str]
    agency_id:           Optional[int]
    agency_name:         str
    posted_date:         Optional[str]


class VendorResponse(ORMBase):
    agency_id:      int
    agency_name:    str
    contract_count: int


class ApplicationResponse(ORMBase):
    id:          int
    source_name: str
    status_code: str
    was_success: bool
    posted_from: str
    posted_to:   str
    fetched_at:  datetime


class HealthResponse(BaseModel):
    status:    str
    timestamp: datetime
