from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./audit_results.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

class AuditResult(Base):
    __tablename__ = "audit_results"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    vendor_name           = Column(String, nullable=True)
    invoice_number        = Column(String, nullable=True)
    audit_date            = Column(DateTime, default=datetime.utcnow)
    estimated_overbill    = Column(Float, nullable=True)
    risk_score            = Column(Integer, nullable=True)
    risk_level            = Column(String, nullable=True)
    findings              = Column(JSON, nullable=True)
    amendment_detected    = Column(Integer, default=0)
    s3_contract_key       = Column(String, nullable=True)
    s3_invoice_key        = Column(String, nullable=True)
    s3_result_key         = Column(String, nullable=True)
    extraction_confidence = Column(Float, nullable=True)

# Create tables automatically
Base.metadata.create_all(bind=engine)