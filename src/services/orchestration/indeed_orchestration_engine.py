import logging
import time
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
from models.configs.indeed_config import IndeedConfig
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from models.enums.element_type import ElementType
from services.misc.database_manager import DatabaseManager
from services.misc.language_parser import LanguageParser
from services.misc.proxy_manager import ProxyManager
from services.misc.selenium_helper import SeleniumHelper
from services.orchestration.abc_orchestration_engine import OrchestrationEngine
from services.pages.indeed_home_page import IndeedHomePage
from services.pages.indeed_login_page import IndeedLoginPage
from services.pages.indeed_one_time_code_page import IndeedOneTimeCodePage
from services.pages.job_listing_pages.indeed_job_listings_page import IndeedJobListingsPage
from services.query_url_builders.indeed_query_url_builder import IndeedQueryUrlBuilder


class IndeedOrchestrationEngine(OrchestrationEngine):
  __indeed_home_page: IndeedHomePage
  __indeed_login_page: IndeedLoginPage
  __indeed_one_time_code_page: IndeedOneTimeCodePage

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    universal_config: UniversalConfig,
    quick_settings: QuickSettings,
    indeed_config: IndeedConfig,
    database_manager: DatabaseManager,
    language_parser: LanguageParser,
    proxy_manager: ProxyManager
  ):
    super().__init__(driver, selenium_helper, universal_config, quick_settings)
    self.__indeed_home_page = IndeedHomePage(selenium_helper)
    self.__indeed_login_page = IndeedLoginPage(driver, selenium_helper, indeed_config)
    self.__indeed_one_time_code_page = IndeedOneTimeCodePage(driver, selenium_helper, indeed_config)
    self._job_listings_page = IndeedJobListingsPage(
      driver,
      selenium_helper,
      database_manager,
      language_parser,
      proxy_manager,
      quick_settings,
      universal_config
    )
    self._query_url_builder = IndeedQueryUrlBuilder(self._universal_config, self._quick_settings)

  def login(self) -> None:
    logging.info("Logging into Indeed...")
    home_url = "https://www.indeed.com"
    self._driver.get(home_url)
    self.__wait_for_security_checkpoint()
    if not "secure.indeed.com/auth" in self._driver.current_url:
      self.__indeed_home_page.navigate_to_login_page()
    self.__indeed_login_page.login()
    while not self.__indeed_one_time_code_page.is_present():
      logging.debug("Waiting for one-time-code page to appear...")
      time.sleep(0.5)
    if self.__indeed_one_time_code_page.can_resolve_with_mail_dot_com():
      logging.info("Attempting to handle one-time-code...")
      time.sleep(1)
      self.__indeed_one_time_code_page.resolve_with_mail_dot_com()
    self.__indeed_one_time_code_page.wait_for_captcha_resolution()

  def get_jobs_parsed_count(self) -> int:
    return self._job_listings_page.get_jobs_parsed_count()

  def reset_jobs_parsed_count(self) -> None:
    self._job_listings_page.reset_jobs_parsed_count()

  def _wait_for_query_url_resolution(self, query_url: str) -> None:
    input("Implement me 4765")

  def _is_security_checkpoint(self) -> bool:
    if self._selenium_helper.exact_text_is_present(
      "Additional Verification Required",
      ElementType.H1
    ):
      return True
    return False

  def __wait_for_security_checkpoint(self, timeout=86400.0) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self._selenium_helper.exact_text_is_present(
        "Additional Verification Required",
        ElementType.H1
      ):
        logging.debug("Waiting for user to resolve security checkpoint...")
        time.sleep(0.5)
      else:
        return
