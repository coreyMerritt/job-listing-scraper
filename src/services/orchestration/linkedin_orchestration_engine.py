import logging
import time
import undetected_chromedriver as uc
from models.configs.linkedin_config import LinkedinConfig
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from services.misc.database_manager import DatabaseManager
from services.misc.proxy_manager import ProxyManager
from services.misc.selenium_helper import SeleniumHelper
from services.orchestration.abc_orchestration_engine import OrchestrationEngine
from services.pages.job_listing_pages.linkedin_job_listings_page import LinkedinJobListingsPage
from services.pages.linkedin_login_page import LinkedinLoginPage
from services.query_url_builders.linkedin_query_url_builder import LinkedinQueryUrlBuilder
from services.misc.language_parser import LanguageParser


class LinkedinOrchestrationEngine(OrchestrationEngine):
  __linkedin_login_page: LinkedinLoginPage

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    database_manager: DatabaseManager,
    language_parser: LanguageParser,
    universal_config: UniversalConfig,
    quick_settings: QuickSettings,
    linkedin_config: LinkedinConfig,
    proxy_manager: ProxyManager
  ):
    super().__init__(driver, selenium_helper, universal_config, quick_settings)
    self.__linkedin_login_page = LinkedinLoginPage(
      driver,
      selenium_helper,
      linkedin_config
    )
    self._job_listings_page = LinkedinJobListingsPage(
      driver,
      selenium_helper,
      database_manager,
      language_parser,
      proxy_manager,
      quick_settings,
      universal_config
    )
    self._query_url_builder = LinkedinQueryUrlBuilder(self._universal_config, self._quick_settings)

  def login(self) -> None:
    logging.debug("Logging into Linkedin...")
    self.__linkedin_login_page.login()

  def get_jobs_parsed_count(self) -> int:
    return self._job_listings_page.get_jobs_parsed_count()

  def reset_jobs_parsed_count(self) -> None:
    self._job_listings_page.reset_jobs_parsed_count()

  def _is_security_checkpoint(self) -> bool:
    input("Implement me 2601")
    return True

  def _go_to_query(self, search_term: str) -> None:
    query_url = self._query_url_builder.build(search_term)
    logging.debug("Going to %s", query_url)
    self._driver.get(query_url)
    while not "linkedin.com/jobs/search" in self._driver.current_url:
      logging.debug("Waiting for url to include: linkedin.com/jobs/search...")
      time.sleep(0.5)

  def _wait_for_query_url_resolution(self, query_url: str) -> None:
    input("Implement me 2937")
