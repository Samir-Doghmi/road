from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Job(Base):
    __tablename__ = "r_jobs"

    job_id = Column(String(36), primary_key=True)
    status = Column(String(50), nullable=False, default="queued") # queued, running, completed, failed
    output_files = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
