from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from models.db.base import Base


class JobApplicationORM(Base):
  __tablename__ = 'job_applications'
  id = Column(Integer, primary_key=True)
  first_name = Column(String)
  last_name = Column(String)
  applied = Column(Boolean)
  ignore_type = Column(String, nullable=True)
  ignore_category = Column(String, nullable=True)
  ignore_term = Column(String, nullable=True)
  timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
  job_listing_id = Column(Integer, ForeignKey('job_listings.id'), nullable=False)
  job_listing = relationship("JobListingORM", back_populates="applications")
