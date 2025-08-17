from abc import ABC, abstractmethod
import time
from typing import Set, Tuple
import logging
import psutil
import undetected_chromedriver as uc
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from entities.job_listings.abc_job_listing import JobListing
from exceptions.glassdoor_zero_jobs_bug_exception import GlassdoorZeroJobsBugException
from exceptions.job_details_didnt_load_exception import JobDetailsDidntLoadException
from exceptions.job_listing_is_advertisement_exception import JobListingIsAdvertisementException
from exceptions.job_listing_opens_in_window_exception import JobListingOpensInWindowException
from exceptions.linkedin_something_went_wrong_div_exception import LinkedinSomethingWentWrongException
from exceptions.memory_overload_exception import MemoryOverloadException
from exceptions.no_more_job_listings_exception import NoMoreJobListingsException
from exceptions.no_results_found_page_exception import NoResultsFoundPageException
from exceptions.page_froze_exception import PageFrozeException
from exceptions.something_went_wrong_page_exception import SomethingWentWrongPageException
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from services.misc.database_manager import DatabaseManager
from services.misc.job_criteria_checker import JobCriteriaChecker
from services.misc.proxy_manager import ProxyManager
from services.misc.selenium_helper import SeleniumHelper
from services.misc.language_parser import LanguageParser


class JobListingsPage(ABC):
  _driver: uc.Chrome
  _selenium_helper: SeleniumHelper
  _criteria_checker: JobCriteriaChecker
  _database_manager: DatabaseManager
  _language_parser: LanguageParser
  _proxy_manager: ProxyManager
  _quick_settings: QuickSettings
  _universal_config: UniversalConfig
  _current_session_jobs: Set[str]
  _jobs_parsed_count: int

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    database_manager: DatabaseManager,
    language_parser: LanguageParser,
    proxy_manager: ProxyManager,
    quick_settings: QuickSettings,
    universal_config: UniversalConfig
  ):
    self._driver = driver
    self._selenium_helper = selenium_helper
    self._criteria_checker = JobCriteriaChecker()
    self._database_manager = database_manager
    self._language_parser = language_parser
    self._proxy_manager = proxy_manager
    self._quick_settings = quick_settings
    self._universal_config = universal_config
    self._current_session_jobs = set()
    self._jobs_parsed_count = 0

  def get_jobs_parsed_count(self) -> int:
    return self._jobs_parsed_count

  def reset_jobs_parsed_count(self) -> None:
    self._jobs_parsed_count = 0

  def scrape_current_query(self) -> None:
    zero_results_count = 0
    while self._is_zero_results():
      zero_results_count += 1
      if zero_results_count > 3:
        logging.info("0 results. Skipping query...")
        return
      else:
        try:
          self._driver.refresh()
        except TimeoutException:
          pass
    total_jobs_tried = 0
    job_listing_li_index = 0
    while True:
      try:
        total_jobs_tried, job_listing_li_index = self._handle_incrementors(total_jobs_tried, job_listing_li_index)
        if not total_jobs_tried == 1:
          if self._need_next_page(job_listing_li_index):
            if self._is_next_page():
              logging.info("Going to next page...")
              self._go_to_next_page()
            else:
              raise NoMoreJobListingsException()
        logging.info("Attempting Job Listing: %s...", f"{total_jobs_tried:,}")
        logging.info("Trying to get Job Listing Li...")
        job_listing_li = self._get_job_listing_li(job_listing_li_index)
        while True:
          try:
            logging.info("Scrolling Job Listing Li into view...")
            self._selenium_helper.scroll_into_view(job_listing_li)
            break
          except StaleElementReferenceException:
            job_listing_li = self._get_job_listing_li(job_listing_li_index)
        while True:
          try:
            logging.info("Building Brief Job Listing...")
            brief_job_listing = self._build_brief_job_listing(job_listing_li)
            break
          except StaleElementReferenceException:
            job_listing_li = self._get_job_listing_li(job_listing_li_index)
        brief_job_listing.print_most()
        if brief_job_listing.to_minimal_str() in self._current_session_jobs:
          logging.info("Ignoring Brief Job Listing because we've already applied this session. Skipping...")
          continue
        logging.info("Adding Brief Job Listing to Current Session Jobs...")
        self._current_session_jobs.add(brief_job_listing.to_minimal_str())
        self._jobs_parsed_count += 1
        if not self._criteria_checker.passes(self._quick_settings, self._universal_config, brief_job_listing):
          logging.info("Ignoring Brief Job Listing because it does not meet ignore/ideal criteria.")
          continue
        if not self._quick_settings.bot_behavior.full_scrape:
          logging.info("Adding Brief Job Listing to database...")
          self._add_job_listing_to_db(brief_job_listing)
          continue
        while True:
          try:
            logging.info("Clicking Job Listing Li...")
            self._click_job(job_listing_li)
            break
          except StaleElementReferenceException:
            job_listing_li = self._get_job_listing_li(job_listing_li_index)
        while True:
          try:
            logging.info("Getting Job Details Div...")
            job_details_div = self._get_job_details_div()
            logging.info("Building Job Listing...")
            job_listing = self._build_job_listing(job_listing_li, job_details_div)
            break
          except JobDetailsDidntLoadException as e:
            if self._quick_settings.bot_behavior.fallback_to_brief_on_load_issues:
              logging.info("Adding Brief Job Listing to database...")
              self._add_job_listing_to_db(brief_job_listing)
            raise e
          except StaleElementReferenceException:
            logging.warning("Stale element while trying to create job listing. Trying again...")
            time.sleep(0.1)
        job_listing.print_most()
        if not self._criteria_checker.passes(self._quick_settings, self._universal_config, job_listing):
          logging.info("Ignoring Job Listing because it does not meet ignore/ideal criteria.")
          continue
        logging.info("Adding Job Listing to Database...")
        self._add_job_listing_to_db(job_listing)
        self._handle_potential_overload()
        self._anti_rate_limit_wait()
      except GlassdoorZeroJobsBugException:
        logging.info("Show more jobs button spawned zero jobs. Refreshing and trying again...")
        while True:
          try:
            self._driver.refresh()
            break
          except TimeoutException:
            pass
        self.scrape_current_query()
        return
      except LinkedinSomethingWentWrongException:
        logging.info("Found something went wrong div. Skipping...")
        continue
      except JobDetailsDidntLoadException:
        logging.warning("Job details didn't load. Skipping...")
        continue
      except JobListingIsAdvertisementException:
        logging.info("Skipping Job Listing because it is an advertisement.")
        continue
      except JobListingOpensInWindowException:
        logging.warning("Alternate render detected. Refreshing and trying again...")
        if len(self._driver.window_handles) > 1:
          self._driver.switch_to.window(self._driver.window_handles[-1])
          self._driver.close()
          self._driver.switch_to.window(self._driver.window_handles[0])
        self._driver.refresh()
        self.scrape_current_query()
        return
      except MemoryOverloadException:
        print(psutil.virtual_memory().percent)
        self._current_session_jobs = set()
        print(psutil.virtual_memory().percent)
        input("How much memory did we save???")
      except NoMoreJobListingsException:
        logging.info("No Job Listings left -- Finished with query.")
        return
      except NoResultsFoundPageException:
        logging.info("Detected No Results Found Page. Refreshing and trying query again...")
        self._driver.refresh()
        self.scrape_current_query()
        return
      except PageFrozeException:
        logging.warning("Pages seems to have froze. Refreshing and trying query again...")
        self._driver.refresh()
        self.scrape_current_query()
        return
      except SomethingWentWrongPageException:
        logging.warning("Something went wrong page detected. Refreshing and trying query again...")
        self._driver.refresh()
        self.scrape_current_query()
        return

  def _handle_potential_overload(self) -> None:
    current_memory_usage = psutil.virtual_memory().percent
    logging.debug("Current memory usage: %s%s", current_memory_usage, "%")
    if current_memory_usage > 90:
      raise MemoryOverloadException()

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
  def _get_job_listings_ul(self, timeout=10.0) -> WebElement:
    pass

  @abstractmethod
  def _build_brief_job_listing(self, job_listing_li: WebElement, timeout=10.0) -> JobListing:
    pass

  @abstractmethod
  def _add_job_listing_to_db(self, job_listing: JobListing) -> None:
    pass

  @abstractmethod
  def _anti_rate_limit_wait(self) -> None:
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
  def _need_next_page(self, job_listing_li_index: int) -> bool:
    pass

  @abstractmethod
  def _is_next_page(self) -> bool:
    pass

  @abstractmethod
  def _go_to_next_page(self) -> None:
    pass
