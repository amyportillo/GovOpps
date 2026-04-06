# database.py
# SQLAlchemy ORM models that match the existing PostgreSQL tables.
# Column names here must match exactly what's in the database.

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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


class Agency(Base):
    __tablename__ = "agency"

    agency_id   = Column(Integer, primary_key=True, autoincrement=True)
    agency_name = Column(Text, nullable=False, unique=True)
    agency_type = Column(Text)
    website     = Column(Text)

    contracts = relationship("Contract", back_populates="agency")


class Contract(Base):
    __tablename__ = "contract"

    contract_id         = Column(Integer, primary_key=True, autoincrement=True)
    title               = Column(Text)
    description         = Column(Text)
    agency_id           = Column(Integer, ForeignKey("agency.agency_id"))
    posted_date         = Column(Text)
    deadline_date       = Column(Text)
    contract_value      = Column(Text)
    status              = Column(Text)
    # These two columns are added by our migration below — they don't exist in the C# schema
    notice_id           = Column(Text)
    solicitation_number = Column(Text)

    agency = relationship("Agency", back_populates="contracts")


class RawApiData(Base):
    __tablename__ = "raw_api_data"

    raw_id        = Column(Integer, primary_key=True, autoincrement=True)
    source_name   = Column(Text, nullable=False)
    raw_json      = Column(JSONB, nullable=False)
    fetched_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status        = Column(Text, nullable=False)
    error_message = Column(Text)


class ApiFetchAudit(Base):
    __tablename__ = "api_fetch_audit"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(Text, nullable=False)
    status_code = Column(Text, nullable=False)
    was_success = Column(Boolean, nullable=False)
    posted_from = Column(Text, nullable=False)
    posted_to   = Column(Text, nullable=False)
    fetched_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ErrorLog(Base):
    __tablename__ = "error_log"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    error_context = Column(Text, nullable=False)
    error_message = Column(Text, nullable=False)
    logged_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def init_db() -> None:
    # Add the two columns the C# schema is missing (safe to run multiple times)
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE contract ADD COLUMN IF NOT EXISTS notice_id TEXT"))
        conn.execute(text("ALTER TABLE contract ADD COLUMN IF NOT EXISTS solicitation_number TEXT"))
        conn.commit()
    print("Database tables verified.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
