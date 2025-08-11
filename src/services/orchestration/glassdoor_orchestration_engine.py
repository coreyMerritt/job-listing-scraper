import logging
import time
import undetected_chromedriver as uc
from selenium.common.exceptions import JavascriptException, TimeoutException
from exceptions.service_is_down_exception import ServiceIsDownException
from models.configs.glassdoor_config import GlassdoorConfig
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from models.enums.element_type import ElementType
from services.misc.database_manager import DatabaseManager
from services.query_url_builders.glassdoor_query_url_builder import GlassdoorQueryUrlBuilder
from services.misc.selenium_helper import SeleniumHelper
from services.pages.glassdoor_login_page import GlassdoorLoginPage
from services.pages.job_listing_pages.glassdoor_job_listings_page import GlassdoorJobListingsPage
from services.misc.language_parser import LanguageParser


class GlassdoorOrchestrationEngine:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __universal_config: UniversalConfig
  __quick_settings: QuickSettings
  __glassdoor_login_page: GlassdoorLoginPage
  __glassdoor_job_listings_page: GlassdoorJobListingsPage

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    database_manager: DatabaseManager,
    language_parser: LanguageParser,
    universal_config: UniversalConfig,
    quick_settings: QuickSettings,
    glassdoor_config: GlassdoorConfig
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__universal_config = universal_config
    self.__quick_settings = quick_settings
    self.__glassdoor_login_page = GlassdoorLoginPage(driver, selenium_helper, glassdoor_config)
    self.__glassdoor_job_listings_page = GlassdoorJobListingsPage(
      driver,
      selenium_helper,
      database_manager,
      language_parser,
      quick_settings,
      universal_config
    )


  def login(self) -> None:
    logging.info("Logging into Glassdoor...")
    base_url = "https://www.glassdoor.com"
    while True:
      try:
        self.__driver.get(base_url)
        self.__wait_for_human_verification_page()
        break
      except TimeoutException:
        logging.warning("Timed out. Trying again...")
        time.sleep(0.5)
    self.__glassdoor_login_page.login()

  def scrape(self) -> None:
    search_terms = self.__universal_config.search.terms.match
    for search_term in search_terms:
      timeout = 60.0
      start_time = time.time()
      while True:
        try:
          while time.time() - start_time < timeout:
            try:
              query_builder = GlassdoorQueryUrlBuilder(self.__universal_config, self.__quick_settings)
              query_url = query_builder.build(search_term)
              self.__go_to_query_url(query_url)
              self.__wait_for_query_url_resolution(query_url)
              self.__glassdoor_job_listings_page.scrape_current_query()
              break
            except TimeoutError:
              logging.warning("Timed out waiting for query url. Trying again...")
              time.sleep(0.1)
            except ServiceIsDownException:
              logging.error("Glassdoor service appears to be down. Skipping all Glassdoor queries...")
              return
          break
        except JavascriptException:
          logging.error("Glassdoor \"Show More Jobs\" button isn't functioning. Trying again...")
          continue

  def __wait_for_human_verification_page(self) -> None:
    while True:
      if self.__selenium_helper.exact_text_is_present(
        "Help Us Protect Glassdoor",
        ElementType.H1
      ):
        logging.info("Waiting for user to solve human verification page...")
        time.sleep(0.5)
        continue
      elif self.__selenium_helper.exact_text_is_present(
        "Enter email",
        ElementType.LABEL
      ):
        break
      logging.info("Waiting for login page to appear...")
      time.sleep(0.5)

  def __go_to_query_url(self, url: str) -> None:
    logging.info("Going to query url: %s...", url)
    try:
      self.__driver.get(url)
    except TimeoutException:
      pass

  def __wait_for_query_url_resolution(self, query_url: str, timeout=15.0) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self.__driver.current_url == query_url:
        return
      logging.info("Waiting for url resoltion...")
      time.sleep(0.5)
    raise TimeoutError("Timed out waiting for query url resolution")
