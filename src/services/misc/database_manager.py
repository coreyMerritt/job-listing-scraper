
from datetime import datetime, timedelta, timezone
import logging
from typing import List, Tuple
from urllib.parse import quote_plus
from sqlalchemy import create_engine, desc, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from entities.job_listings.abc_job_listing import JobListing
from entities.job_application import JobApplication
from models.configs.system_config import DatabaseConfig
from models.db.job_application_orm import JobApplicationORM
from models.db.base import Base
from models.db.job_listing_orm import JobListingORM
from models.db.rate_limit_orm import RateLimitORM
from models.db.system_record_orm import SystemRecordORM
from models.enums.platform import Platform


class DatabaseManager:
  __engine: Engine
  __session_factory: sessionmaker

  def __init__(self, database_config: DatabaseConfig):
    engine = database_config.engine
    username = database_config.username
    password = quote_plus(database_config.password)
    host = database_config.host
    port = database_config.port
    name = database_config.name
    self.__engine = create_engine(f"{engine}://{username}:{password}@{host}:{port}/{name}")
    Base.metadata.create_all(self.__engine)
    self.__session_factory = sessionmaker(bind=self.__engine)

  def get_session(self) -> Session:
    return self.__session_factory()

  def is_job_listing(
    self,
    job_listing: JobListing,
    platform: Platform
  ) -> bool:
    job_listing_orm = self.__build_job_listing_orm(job_listing, platform)
    with self.get_session() as session:
      job_listing_entry = session.query(JobListingORM).filter_by(
        job_title=job_listing_orm.job_title,
        company=job_listing_orm.company,
        location=job_listing_orm.location,
        platform=platform.value,
      ).first()
    if job_listing_entry:
      return True
    return False

  def create_new_job_listing(
    self,
    job_listing: JobListing,
    platform: Platform
  ) -> None:
    job_listing_orm = self.__build_job_listing_orm(job_listing, platform)
    with self.get_session() as session:
      job_listing_entry = session.query(JobListingORM).filter_by(
        job_title=job_listing_orm.job_title,
        company=job_listing_orm.company,
        location=job_listing_orm.location,
        platform=platform.value,
      ).first()
      if job_listing_entry:
        if job_listing_entry.min_pay != job_listing.get_min_pay():
          job_listing_entry.min_pay = job_listing.get_min_pay()
        if job_listing_entry.max_pay != job_listing.get_max_pay():
          job_listing_entry.max_pay = job_listing.get_max_pay()
        if job_listing_entry.min_yoe != job_listing.get_min_yoe():
          job_listing_entry.min_yoe = job_listing.get_min_yoe()
        if job_listing_entry.max_yoe != job_listing.get_max_yoe():
          job_listing_entry.max_yoe = job_listing.get_max_yoe()
        if job_listing_entry.description != job_listing.get_description():
          job_listing_entry.description = job_listing.get_description()
        if job_listing_entry.url != job_listing.get_url():
          job_listing_entry.url = job_listing.get_url()
        if job_listing_entry.post_time != job_listing.get_post_time():
          job_listing_entry.post_time = job_listing.get_post_time()
        session.commit()
      else:
        session.add(job_listing_orm)
        session.commit()

  def get_highest_job_listing_ignore_keywords(self, limit=10) -> List[Tuple[str, str, str, int]]:
    with self.get_session() as session:
      top_ignore_terms_query = (
        session.query(
          JobApplicationORM.ignore_type,
          JobApplicationORM.ignore_category,
          JobApplicationORM.ignore_term,
          func.count(JobApplicationORM.id).label("count")    # pylint: disable=not-callable
        )
        .filter(JobApplicationORM.ignore_type.isnot(None))
        .filter(JobApplicationORM.ignore_category.isnot(None))
        .filter(JobApplicationORM.ignore_term.isnot(None))
        .group_by(
          JobApplicationORM.ignore_type,
          JobApplicationORM.ignore_category,
          JobApplicationORM.ignore_term
        )
        .order_by(func.count(JobApplicationORM.id).desc())   # pylint: disable=not-callable
        .limit(limit)
      )
      top_ignore_terms = top_ignore_terms_query.all()
      return top_ignore_terms

  def log_rate_limit_block(self, ip_address: str, platform: Platform) -> None:
    logging.warning("Rate limited by %s on address: %s", platform.value, ip_address)
    rate_limit_orm = RateLimitORM(
      ip_address=ip_address,
      platform=platform.value
    )
    with self.get_session() as session:
      session.add(rate_limit_orm)
      session.commit()

  def get_rate_limit_time_delta(self, ip_address: str, platform: Platform | None = None) -> timedelta:
    with self.get_session() as session:
      if platform:
        last_rate_limit_from_host = (
          session.query(RateLimitORM)
            .filter(RateLimitORM.ip_address == ip_address)
            .filter(RateLimitORM.platform == platform.value)
            .order_by(desc(RateLimitORM.timestamp))
            .first()
        )
      else:
        last_rate_limit_from_host = (
          session.query(RateLimitORM)
            .filter(RateLimitORM.ip_address == ip_address)
            .order_by(desc(RateLimitORM.timestamp))
            .first()
        )
    if last_rate_limit_from_host is None:
      return timedelta.max
    assert isinstance(last_rate_limit_from_host, RateLimitORM)
    last_logged_rate_limit_timestamp = last_rate_limit_from_host.timestamp
    assert isinstance(last_logged_rate_limit_timestamp, datetime)
    now = datetime.now(timezone.utc)
    time_delta = now - last_logged_rate_limit_timestamp
    return time_delta

  def log_system_record(
    self,
    address: str,
    jobs_parsed: int,
    platforms: str,
    happy_exit: bool,
    start_time: datetime,
    end_time: datetime
  ) -> None:
    system_record_orm = SystemRecordORM(
      address=address,
      jobs_parsed=jobs_parsed,
      platforms=platforms,
      happy_exit=happy_exit,
      start_time=start_time,
      end_time=end_time
    )
    with self.get_session() as session:
      session.add(system_record_orm)
      session.commit()

  def get_last_system_record(self) -> SystemRecordORM | None:
    with self.get_session() as session:
      last_system_record_orm = (
        session.query(SystemRecordORM)
          .order_by(desc(SystemRecordORM.start_time))
          .first()
      )
    return last_system_record_orm

  def __build_job_listing_orm(self, job_listing: JobListing, platform: Platform) -> JobListingORM:
    job_listing_orm = JobListingORM(
      job_title=job_listing.get_title(),
      company=job_listing.get_company(),
      location=job_listing.get_location(),
      min_pay=job_listing.get_min_pay(),
      max_pay=job_listing.get_max_pay(),
      min_yoe=job_listing.get_min_yoe(),
      max_yoe=job_listing.get_max_yoe(),
      description=job_listing.get_description(),
      platform=platform.value,
      url=job_listing.get_url(),
      post_time=job_listing.get_post_time()
    )
    return job_listing_orm
