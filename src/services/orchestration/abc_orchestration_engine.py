from abc import ABC, abstractmethod
import logging
import time
import undetected_chromedriver as uc
from selenium.common.exceptions import JavascriptException, TimeoutException
from exceptions.not_logged_in_exception import NotLoggedInException
from exceptions.service_is_down_exception import ServiceIsDownException
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from services.misc.selenium_helper import SeleniumHelper
from services.pages.job_listing_pages.abc_job_listings_page import JobListingsPage
from services.query_url_builders.abc_query_url_builder import QueryUrlBuilder


class OrchestrationEngine(ABC):
  _driver: uc.Chrome
  _selenium_helper: SeleniumHelper
  _universal_config: UniversalConfig
  _quick_settings: QuickSettings
  _query_url_builder: QueryUrlBuilder
  _job_listings_page: JobListingsPage

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    universal_config: UniversalConfig,
    quick_settings: QuickSettings
  ):
    self._driver = driver
    self._selenium_helper = selenium_helper
    self._universal_config = universal_config
    self._quick_settings = quick_settings
    # self._query_url_builder = SomeQueryUrlBuilder(...)
    # self._job_listings_page = SomeJobListingsPage(...)

  def scrape(self) -> None:
    search_terms = self._universal_config.search.terms.match
    for search_term in search_terms:
      timeout = 60.0
      start_time = time.time()
      while True:
        try:
          while time.time() - start_time < timeout:
            try:
              query_url = self._query_url_builder.build(search_term)
              self._go_to_query_url(query_url)
              while self._is_security_checkpoint():
                time.sleep(0.5)
                logging.info("Waiting for user to solve security checkpoint...")
              self._wait_for_query_url_resolution(query_url)
              self._job_listings_page.scrape_current_query()
              break
            except TimeoutError:
              logging.warning("Timed out waiting for query url. Trying again...")
              time.sleep(0.1)
            except NotLoggedInException:
              self.login()
            except ServiceIsDownException:
              logging.error("Glassdoor service appears to be down. Skipping all Glassdoor queries...")
              return
          break
        except JavascriptException:
          logging.error("Glassdoor \"Show More Jobs\" button isn't functioning. Trying again...")
          continue

  def _go_to_query_url(self, url: str) -> None:
    logging.info("Going to query url: %s...", url)
    try:
      self._driver.get(url)
    except TimeoutException:
      pass

  @abstractmethod
  def _wait_for_query_url_resolution(self, query_url: str) -> None:
    pass

  @abstractmethod
  def login(self) -> None:
    pass

  @abstractmethod
  def get_jobs_parsed_count(self) -> int:
    pass

  @abstractmethod
  def reset_jobs_parsed_count(self) -> None:
    pass

  @abstractmethod
  def _is_security_checkpoint(self) -> bool:
    pass
