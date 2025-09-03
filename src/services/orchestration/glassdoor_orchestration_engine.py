import logging
import time
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
from models.configs.glassdoor_config import GlassdoorConfig
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from models.enums.element_type import ElementType
from services.misc.database_manager import DatabaseManager
from services.misc.proxy_manager import ProxyManager
from services.orchestration.abc_orchestration_engine import OrchestrationEngine
from services.query_url_builders.glassdoor_query_url_builder import GlassdoorQueryUrlBuilder
from services.misc.selenium_helper import SeleniumHelper
from services.pages.glassdoor_login_page import GlassdoorLoginPage
from services.pages.job_listing_pages.glassdoor_job_listings_page import GlassdoorJobListingsPage
from services.misc.language_parser import LanguageParser


class GlassdoorOrchestrationEngine(OrchestrationEngine):
  __glassdoor_login_page: GlassdoorLoginPage

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    database_manager: DatabaseManager,
    language_parser: LanguageParser,
    proxy_manager: ProxyManager,
    universal_config: UniversalConfig,
    quick_settings: QuickSettings,
    glassdoor_config: GlassdoorConfig
  ):
    super().__init__(driver, selenium_helper, universal_config, quick_settings)
    self.__glassdoor_login_page = GlassdoorLoginPage(driver, selenium_helper, glassdoor_config)
    self._job_listings_page = GlassdoorJobListingsPage(
      driver,
      selenium_helper,
      database_manager,
      language_parser,
      proxy_manager,
      quick_settings,
      universal_config
    )
    self._query_url_builder = GlassdoorQueryUrlBuilder(self._universal_config, self._quick_settings)

  def login(self) -> None:
    logging.info("Logging into Glassdoor...")
    base_url = "https://www.glassdoor.com"
    while True:
      try:
        self._driver.get(base_url)
        self.__wait_for_human_verification_page()
        break
      except TimeoutException:
        logging.warning("Timed out. Trying again...")
        time.sleep(0.5)
    self.__glassdoor_login_page.login()

  def get_jobs_parsed_count(self) -> int:
    return self._job_listings_page.get_jobs_parsed_count()

  def reset_jobs_parsed_count(self) -> None:
    self._job_listings_page.reset_jobs_parsed_count()

  def _is_security_checkpoint(self) -> bool:
    return self._selenium_helper.exact_text_is_present(
      "Help Us Protect Glassdoor",
      ElementType.H1
    )

  def __wait_for_human_verification_page(self) -> None:
    while True:
      if self._selenium_helper.exact_text_is_present(
        "Help Us Protect Glassdoor",
        ElementType.H1
      ):
        logging.info("Waiting for user to solve human verification page...")
        time.sleep(0.5)
        continue
      elif self._selenium_helper.exact_text_is_present(
        "Enter email",
        ElementType.LABEL
      ):
        break
      logging.info("Waiting for login page to appear...")
      time.sleep(0.5)

  def _wait_for_query_url_resolution(self, query_url: str, timeout=15.0) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self._driver.current_url == query_url:
        return
      logging.info("Waiting for url resoltion...")
      time.sleep(0.5)
    raise TimeoutError("Timed out waiting for query url resolution")
