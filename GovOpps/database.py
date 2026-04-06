# database.py
# SQLAlchemy ORM models that match the existing PostgreSQL tables.
# Column names here must match exactly what's in the database.
#
# ORM = Object-Relational Mapper. Instead of writing raw SQL like
# "SELECT * FROM contract", you write Python like db.query(Contract).all()
# and SQLAlchemy handles the translation to SQL behind the scenes.

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB  # Postgres-specific binary JSON column type
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from config import settings


# create_engine builds the connection pool to PostgreSQL using the URL from config.
# pool_pre_ping=True tells SQLAlchemy to test each connection before using it —
# this prevents crashes from connections that went stale (e.g. after the DB restarted).
engine = create_engine(settings.database_url, pool_pre_ping=True)

# sessionmaker creates a factory for database sessions.
# A session is a temporary workspace for your queries — like a transaction.
# You add/query things, then either commit (save to disk) or rollback (undo).
# autocommit=False  → you must call db.commit() yourself; nothing auto-saves.
# autoflush=False   → SQLAlchemy won't silently flush pending changes mid-session.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Base is the parent class all our table models inherit from.
# It holds a registry of every table SQLAlchemy knows about in this project.
class Base(DeclarativeBase):
    pass


class Agency(Base):
    # Each class that inherits Base maps to exactly one table in the database.
    __tablename__ = "agency"

    # primary_key=True   → this column uniquely identifies each row.
    # autoincrement=True → the database assigns IDs automatically (1, 2, 3...).
    agency_id   = Column(Integer, primary_key=True, autoincrement=True)

    # nullable=False → this column must always have a value; the DB rejects rows without it.
    # unique=True    → no two agencies can share the same name.
    agency_name = Column(Text, nullable=False, unique=True)
    agency_type = Column(Text)
    website     = Column(Text)

    # This is NOT a real database column — it's a SQLAlchemy "relationship".
    # It lets you write agency.contracts to get all contracts for this agency
    # without writing a JOIN yourself. SQLAlchemy generates the JOIN internally.
    # back_populates="agency" wires up the reverse side on the Contract model.
    contracts = relationship("Contract", back_populates="agency")


class Contract(Base):
    __tablename__ = "contract"

    contract_id         = Column(Integer, primary_key=True, autoincrement=True)
    title               = Column(Text)
    description         = Column(Text)

    # ForeignKey("agency.agency_id") links this column to the agency table.
    # The DB enforces this — you can't insert a contract with an agency_id that
    # doesn't exist in the agency table.
    agency_id           = Column(Integer, ForeignKey("agency.agency_id"))

    posted_date         = Column(Text)
    deadline_date       = Column(Text)
    contract_value      = Column(Text)
    status              = Column(Text)

    # These two columns are added by our migration below — they don't exist in the C# schema.
    notice_id           = Column(Text)   # SAM.gov's unique ID for this opportunity
    solicitation_number = Column(Text)   # the government's reference number for the contract

    # Reverse side of Agency.contracts. Lets you do contract.agency to get
    # the full Agency object without writing a JOIN.
    agency = relationship("Agency", back_populates="contracts")


class RawApiData(Base):
    # Stores the raw, unmodified JSON response from SAM.gov before we parse it.
    # This is a safety net — if our parsing logic breaks, we can look back at
    # exactly what the API returned and re-process it without calling the API again.
    __tablename__ = "raw_api_data"

    raw_id        = Column(Integer, primary_key=True, autoincrement=True)
    source_name   = Column(Text, nullable=False)  # always "SAM.gov"

    # JSONB stores JSON as binary in Postgres — faster to query than plain TEXT
    # and supports indexing on individual JSON keys if needed later.
    raw_json      = Column(JSONB, nullable=False)

    # server_default=func.now() means the database sets this timestamp automatically
    # at insert time. You don't pass it from Python — the DB handles it.
    fetched_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    status        = Column(Text, nullable=False)  # "Success" or "Failed"
    error_message = Column(Text)                  # only populated when status is "Failed"


class ApiFetchAudit(Base):
    # A log of every ETL run — one row per run.
    # Lets you see the full history of when data was fetched, whether it worked,
    # and what date range was requested.
    __tablename__ = "api_fetch_audit"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(Text, nullable=False)    # always "SAM.gov"
    status_code = Column(Text, nullable=False)    # HTTP response code as a string, e.g. "200"
    was_success = Column(Boolean, nullable=False) # True if the API call returned HTTP 2xx
    posted_from = Column(Text, nullable=False)    # start of the date range we requested
    posted_to   = Column(Text, nullable=False)    # end of the date range we requested
    fetched_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ErrorLog(Base):
    # Any unexpected errors during ETL processing get written here.
    # Makes it easy to review what went wrong without digging through terminal output.
    __tablename__ = "error_log"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    error_context = Column(Text, nullable=False)  # where the error happened, e.g. "API Fetch"
    error_message = Column(Text, nullable=False)  # the actual error text
    logged_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def init_db() -> None:
    # Adds the two columns that didn't exist in the original C# database schema.
    # "ADD COLUMN IF NOT EXISTS" makes this completely safe to call on every startup —
    # if the columns are already there, nothing happens. If they're missing, they get added.
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE contract ADD COLUMN IF NOT EXISTS notice_id TEXT"))
        conn.execute(text("ALTER TABLE contract ADD COLUMN IF NOT EXISTS solicitation_number TEXT"))
        conn.commit()
    print("Database tables verified.")


def get_db():
    # A generator function used as a FastAPI dependency (see api.py).
    # FastAPI calls this, runs up to "yield", and injects the db session into your route function.
    # After the route finishes — whether it succeeds or crashes — execution resumes after yield,
    # so db.close() ALWAYS runs. This is critical: without it, connections would pile up and
    # eventually exhaust the connection pool.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
