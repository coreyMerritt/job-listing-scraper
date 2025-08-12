import logging
import time
import undetected_chromedriver as uc
from selenium.common.exceptions import JavascriptException, TimeoutException
from exceptions.service_is_down_exception import ServiceIsDownException
from models.configs.indeed_config import IndeedConfig
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from services.misc.database_manager import DatabaseManager
from services.misc.proxy_manager import ProxyManager
from services.misc.selenium_helper import SeleniumHelper
from services.pages.indeed_login_page import IndeedLoginPage
from services.pages.indeed_one_time_code_page import IndeedOneTimeCodePage
from services.pages.job_listing_pages.indeed_job_listings_page import IndeedJobListingsPage
from services.query_url_builders.indeed_query_url_builder import IndeedQueryUrlBuilder
from services.misc.language_parser import LanguageParser


class IndeedOrchestrationEngine:
  __driver: uc.Chrome
  __universal_config: UniversalConfig
  __indeed_login_page: IndeedLoginPage
  __indeed_one_time_code_page: IndeedOneTimeCodePage
  __indeed_job_listings_page: IndeedJobListingsPage

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    database_manager: DatabaseManager,
    language_parser: LanguageParser,
    proxy_manager: ProxyManager,
    universal_config: UniversalConfig,
    quick_settings: QuickSettings,
    indeed_config: IndeedConfig
  ):
    self.__driver = driver
    self.__universal_config = universal_config
    self.__indeed_login_page = IndeedLoginPage(driver, selenium_helper, indeed_config)
    self.__indeed_one_time_code_page = IndeedOneTimeCodePage(driver, selenium_helper, indeed_config)
    self.__indeed_job_listings_page = IndeedJobListingsPage(
      driver,
      selenium_helper,
      database_manager,
      language_parser,
      proxy_manager,
      quick_settings,
      universal_config
    )

  def login(self) -> None:
    base_url = "https://www.indeed.com"
    logging.debug("Logging into %s...", base_url)
    self.__indeed_login_page.login()
    while not self.__indeed_one_time_code_page.is_present():
      logging.debug("Waiting for one-time-code page to appear...")
      time.sleep(0.5)
    if self.__indeed_one_time_code_page.can_resolve_with_mail_dot_com():
      time.sleep(1)
      self.__indeed_one_time_code_page.resolve_with_mail_dot_com()
    self.__indeed_one_time_code_page.wait_for_captcha_resolution()

  # def scrape(self) -> None:
  #   self.__go_to_query()
  #   while not self.__indeed_job_listings_page.is_present():
  #     logging.debug("Waiting for Job Listings page to appear...")
  #     time.sleep(0.5)
  #   self.__indeed_job_listings_page.scrape_current_query()

  def scrape(self) -> None:
    search_terms = self.__universal_config.search.terms.match
    for search_term in search_terms:
      timeout = 60.0
      start_time = time.time()
      while time.time() - start_time < timeout:
        try:
          query_builder = IndeedQueryUrlBuilder(self.__universal_config)
          query_url = query_builder.build(search_term)
          self.__go_to_query_url(query_url)
          self.__indeed_job_listings_page.scrape_current_query()
          break
        except TimeoutError:
          logging.warning("Timed out waiting for query url. Trying again...")
          time.sleep(0.1)
      break

  def __go_to_query_url(self, url: str) -> None:
    logging.info("Going to query url: %s...", url)
    try:
      self.__driver.get(url)
    except TimeoutException:
      pass

  # def __go_to_query(self) -> None:
  #   query_url_builder = IndeedQueryUrlBuilder(self.__universal_config)
  #   query_url = query_url_builder.build()
  #   logging.debug("Going to %s...",  query_url)
  #   self.__driver.get(query_url)
  #   verification_element_name = "q"
  #   while True:
  #     try:
  #       self.__driver.find_element(By.NAME, verification_element_name)
  #       break
  #     except NoSuchElementException:
  #       logging.debug("Waiting for page verification element to appear...")
  #       time.sleep(0.5)
