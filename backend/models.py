from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from .database import Base
except ImportError:
    from database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    status = Column(String(32), nullable=False, default="created")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    files = relationship("UploadFile", back_populates="job", cascade="all, delete-orphan")

class UploadFile(Base):
    __tablename__ = "upload_files"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=True)
    object_key = Column(String(500), nullable=False)
    status = Column(String(32), nullable=False, default="uploaded")
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("Job", back_populates="files")
