from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String
from models.db.base import Base


class RateLimitORM(Base):
  __tablename__ = 'rate_limits'
  id = Column(Integer, primary_key=True)
  ip_address = Column(String)
  platform = Column(String)
  timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
