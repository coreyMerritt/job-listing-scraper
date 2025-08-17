from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from models.db.base import Base


class SystemRecordORM(Base):
  __tablename__ = 'system_records'
  id = Column(Integer, primary_key=True)
  address = Column(String)
  jobs_parsed = Column(Integer)
  platforms = Column(String)
  happy_exit = Column(Boolean)
  start_time = Column(DateTime(timezone=True))
  end_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
