import logging
import time
import undetected_chromedriver as uc
from exceptions.unknown_page_exception import UnknownPageException
from models.configs.linkedin_config import LinkedinConfig
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from services.misc.database_manager import DatabaseManager
from services.misc.proxy_manager import ProxyManager
from services.misc.selenium_helper import SeleniumHelper
from services.pages.job_listing_pages.linkedin_job_listings_page_1 import LinkedinJobListingsPage1
from services.pages.job_listing_pages.linkedin_job_listings_page_2 import LinkedinJobListingsPage2
from services.pages.linkedin_login_page import LinkedinLoginPage
from services.query_url_builders.linkedin_query_url_builder import LinkedinQueryUrlBuilder
from services.misc.language_parser import LanguageParser


class LinkedinOrchestrationEngine:
  __driver: uc.Chrome
  __universal_config: UniversalConfig
  __quick_settings: QuickSettings
  __linkedin_login_page: LinkedinLoginPage
  __linkedin_job_listings_page_1: LinkedinJobListingsPage1
  __linkedin_job_listings_page_2: LinkedinJobListingsPage2

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
    self.__driver = driver
    self.__universal_config = universal_config
    self.__quick_settings = quick_settings
    self.__linkedin_login_page = LinkedinLoginPage(
      driver,
      selenium_helper,
      linkedin_config
    )
    self.__linkedin_job_listings_page_1 = LinkedinJobListingsPage1(
      driver,
      selenium_helper,
      database_manager,
      language_parser,
      proxy_manager,
      quick_settings,
      universal_config
    )
    self.__linkedin_job_listings_page_2 = LinkedinJobListingsPage2(
      driver,
      selenium_helper,
      database_manager,
      language_parser,
      proxy_manager,
      quick_settings,
      universal_config
    )

  def login(self) -> None:
    logging.debug("Logging into Linkedin...")
    self.__linkedin_login_page.login()

  def scrape(self) -> None:
    query_terms = self.__universal_config.search.terms.match
    if not query_terms or len(query_terms) == 0:
      query_terms = [""]
    for search_term in query_terms:
      self.__go_to_query(search_term)
      if self.__linkedin_job_listings_page_1.is_present():
        self.__linkedin_job_listings_page_1.scrape_current_query()
      elif self.__linkedin_job_listings_page_2.is_present():
        self.__linkedin_job_listings_page_2.scrape_current_query()
      else:
        raise UnknownPageException()

  def __go_to_query(self, search_term: str) -> None:
    query_url_builder = LinkedinQueryUrlBuilder(self.__universal_config, self.__quick_settings)
    query_url = query_url_builder.build(search_term)
    logging.debug("Going to %s", query_url)
    self.__driver.get(query_url)
    while not "linkedin.com/jobs/search" in self.__driver.current_url:
      logging.debug("Waiting for url to include: linkedin.com/jobs/search...")
      time.sleep(0.5)
