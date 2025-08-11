from abc import ABC, abstractmethod
import logging
from typing import Set, Tuple
import undetected_chromedriver as uc
from selenium.webdriver.remote.webelement import WebElement
from entities.abc_job_listing import JobListing
from exceptions.job_details_didnt_load_exception import JobDetailsDidntLoadException
from exceptions.job_listing_is_advertisement_exception import JobListingIsAdvertisementException
from exceptions.no_more_job_listings_exception import NoMoreJobListingsException
from exceptions.page_froze_exception import PageFrozeException
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from services.misc.database_manager import DatabaseManager
from services.misc.job_criteria_checker import JobCriteriaChecker
from services.misc.selenium_helper import SeleniumHelper
from services.misc.language_parser import LanguageParser


class JobListingsPage(ABC):
  _driver: uc.Chrome
  _selenium_helper: SeleniumHelper
  _database_manager: DatabaseManager
  _language_parser: LanguageParser
  _criteria_checker: JobCriteriaChecker
  _quick_settings: QuickSettings
  _universal_config: UniversalConfig
  _current_session_jobs: Set[str]

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    database_manager: DatabaseManager,
    language_parser: LanguageParser,
    quick_settings: QuickSettings,
    universal_config: UniversalConfig
  ):
    self._driver = driver
    self._selenium_helper = selenium_helper
    self._database_manager = database_manager
    self._language_parser = language_parser
    self._criteria_checker = JobCriteriaChecker()
    self._quick_settings = quick_settings
    self._universal_config = universal_config
    self._current_session_jobs = set()

  def scrape_current_query(self) -> None:
    if self._is_zero_results():
      logging.info("0 results. Skipping query...")
      return
    total_jobs_tried = 0
    job_listing_li_index = 0
    while True:
      total_jobs_tried, job_listing_li_index = self._handle_incrementors(total_jobs_tried, job_listing_li_index)
      logging.info("Attempting Job Listing: %s...", total_jobs_tried)
      logging.info("Trying to get Job Listing Li...")
      try:
        job_listing_li = self._get_job_listing_li(job_listing_li_index)
      except JobListingIsAdvertisementException:
        logging.info("Skipping Job Listing because it is an advertisement.")
        continue
      except NoMoreJobListingsException:
        if self._is_next_page():
          self._go_to_next_page()
          continue  # TODO: Because of how Glassdoor functions, this causes a bug where Glassdoor skips 1/x listings
        else:
          logging.info("No Job Listings left -- Finished with query.")
          return
      logging.info("Scrolling Job Listing Li into view...")
      self._selenium_helper.scroll_into_view(job_listing_li)
      logging.info("Building Brief Job Listing...")
      brief_job_listing = self._build_brief_job_listing(job_listing_li)
      brief_job_listing.print()
      if brief_job_listing.to_minimal_str() in self._current_session_jobs:
        logging.info("Ignoring Brief Job Listing because we've already applied this session. Skipping...")
        continue
      logging.info("Adding Brief Job Listing to Current Session Jobs...")
      self._current_session_jobs.add(brief_job_listing.to_minimal_str())
      if not self._criteria_checker.passes(self._quick_settings, self._universal_config, brief_job_listing):
        logging.info("Ignoring Brief Job Listing because it does not meet ignore/ideal criteria.")
        continue
      if not self._quick_settings.bot_behavior.full_scrape:
        logging.info("Adding Brief Job Listing to database...")
        self._add_job_listing_to_db(brief_job_listing)
        continue
      try:
        logging.info("Clicking Job Listing Li...")
        self._click_job(job_listing_li)
      except PageFrozeException:
        logging.warning("Pages seems to have froze. Refreshing and trying query again...")
        self._driver.refresh()
        self.scrape_current_query()
        return
      try:
        logging.info("Getting Job Details Div...")
        job_details_div = self._get_job_details_div()
        logging.info("Building Job Listing...")
        job_listing = self._build_job_listing(job_listing_li, job_details_div)
      except JobDetailsDidntLoadException:
        logging.warning("Job Details failed to load. Skipping...")
        continue
      if not self._criteria_checker.passes(self._quick_settings, self._universal_config, job_listing):
        logging.info("Ignoring Job Listing because it does not meet ignore/ideal criteria.")
        continue
      logging.info("Adding Job Listing to Database...")
      self._add_job_listing_to_db(job_listing)
      self._handle_potential_overload()

  @abstractmethod
  def _is_zero_results(self, timeout=10.0) -> bool:
    pass

  @abstractmethod
  def _handle_incrementors(self, total_jobs_tried: int, job_listing_li_index: int) -> Tuple[int, int]:
    pass

  @abstractmethod
  def _get_job_listing_li(self, job_listing_li_index: int, timeout=10.0) -> WebElement:
    pass

  @abstractmethod
  def _is_next_page(self) -> bool:
    pass

  @abstractmethod
  def _go_to_next_page(self) -> None:
    pass

  @abstractmethod
  def _build_brief_job_listing(self, job_listing_li: WebElement, timeout=10.0) -> JobListing:
    pass

  @abstractmethod
  def _add_job_listing_to_db(self, job_listing: JobListing) -> None:
    pass

  @abstractmethod
  def _click_job(self, job_listing_li: WebElement, timeout=10.0) -> None:
    pass

  @abstractmethod
  def _get_job_details_div(self, timeout=30.0) -> WebElement:
    pass

  @abstractmethod
  def _build_job_listing(self, job_listing_li: WebElement, job_details_div: WebElement, timeout=10.0) -> JobListing:
    pass

  @abstractmethod
  def _handle_potential_overload(self) -> None:
    pass
