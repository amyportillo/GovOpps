# database.py
# This file does two things:
#   1. Defines what our database tables look like using SQLAlchemy ORM models
#   2. Creates those tables in PostgreSQL if they don't exist yet
#
# SQLAlchemy ORM lets you work with database rows as Python objects instead of
# writing raw SQL everywhere. Each class below = one table in the database.

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from config import settings


# create_engine builds the actual connection pool to PostgreSQL
# pool_pre_ping=True tests the connection before using it, which prevents
# errors if the database restarted or the connection went idle
engine = create_engine(settings.database_url, pool_pre_ping=True)

# SessionLocal is a factory - every time you call SessionLocal() you get
# a new database session (like a transaction) that you can query and commit
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# All ORM model classes must inherit from this Base class
# SQLAlchemy uses it to keep track of all your table definitions
class Base(DeclarativeBase):
    pass


# Maps to the "agency" table - stores government agencies that post contracts
# This is the same table the C# DatabaseManager created
class Agency(Base):
    __tablename__ = "agency"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(Text, nullable=False, unique=True)
    # server_default means PostgreSQL sets this automatically, not Python
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # This sets up a Python-level link so you can do agency.contracts to get
    # all contracts for that agency without writing a JOIN query manually
    contracts  = relationship("Contract", back_populates="agency")


# Maps to the "contract" table - one row per SAM.gov contract opportunity
class Contract(Base):
    __tablename__ = "contract"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    notice_id            = Column(Text, nullable=False, unique=True)
    title                = Column(Text)
    solicitation_number  = Column(Text)
    # ForeignKey links this to the agency table - every contract belongs to one agency
    agency_id            = Column(Integer, ForeignKey("agency.id"))
    posted_date          = Column(Text)
    created_at           = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # The reverse side of the relationship defined in Agency above
    agency = relationship("Agency", back_populates="contracts")


# Maps to the "raw_api_data" table - saves the exact JSON we got from the API
# This is our safety net: if parsing fails later we still have the original data
class RawApiData(Base):
    __tablename__ = "raw_api_data"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    source_name   = Column(Text, nullable=False)
    # JSONB is a PostgreSQL-specific column type that stores JSON in binary format
    # It's faster to query than plain TEXT and supports JSON operators in SQL
    raw_json      = Column(JSONB, nullable=False)
    status        = Column(Text, nullable=False)
    error_message = Column(Text)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# Maps to the "api_fetch_audit" table - logs every time the ETL script runs
# Useful for tracking whether fetches succeeded and what date range they covered
class ApiFetchAudit(Base):
    __tablename__ = "api_fetch_audit"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(Text, nullable=False)
    status_code = Column(Text, nullable=False)
    was_success = Column(Boolean, nullable=False)
    posted_from = Column(Text, nullable=False)
    posted_to   = Column(Text, nullable=False)
    fetched_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# Maps to the "error_log" table - any exception caught during ETL gets stored here
# Much better than just printing to the console where it could get lost
class ErrorLog(Base):
    __tablename__ = "error_log"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    error_context = Column(Text, nullable=False)
    error_message = Column(Text, nullable=False)
    logged_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def init_db() -> None:
    # create_all checks each table and only creates it if it doesn't exist yet
    # So if your C# project already created these tables, nothing will change
    # and all your existing data will still be there
    Base.metadata.create_all(bind=engine)
    print("Database tables verified / created.")


def get_db():
    # This is a FastAPI dependency - it yields a database session for each request
    # and guarantees the session is closed when the request finishes, even if it crashes
    # Usage in api.py:  db: Session = Depends(get_db)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()