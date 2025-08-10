#!/usr/bin/env python3

import argparse
import logging
import time
import traceback
import yaml
import undetected_chromedriver as uc
from dacite import from_dict
from models.configs.full_config import FullConfig
from models.enums.platform import Platform
from services.misc.database_manager import DatabaseManager
from services.misc.proxy_manager import ProxyManager
from services.misc.selenium_helper import SeleniumHelper
from services.orchestration.glassdoor_orchestration_engine import GlassdoorOrchestrationEngine
from services.orchestration.indeed_orchestration_engine import IndeedOrchestrationEngine
from services.orchestration.linkedin_orchestration_engine import LinkedinOrchestrationEngine
from services.pages.indeed_apply_now_page.indeed_apply_now_page import IndeedApplyNowPage
from services.misc.language_parser import LanguageParser


class Start:
  __config: FullConfig
  __driver: uc.Chrome
  __proxy_manager: ProxyManager
  __selenium_helper: SeleniumHelper
  __database_manager: DatabaseManager
  __indeed_orchestration_engine: IndeedOrchestrationEngine
  __glassdoor_orchestration_engine: GlassdoorOrchestrationEngine
  __linkedin_orchestration_engine: LinkedinOrchestrationEngine
  __language_parser: LanguageParser

  def __init__(self):
    self.__configure_logger()
    with open("config.yml", "r", encoding='utf-8') as config_file:
      raw_config = yaml.safe_load(config_file)
    self.__config = from_dict(data_class=FullConfig, data=raw_config)
    self.__database_manager = DatabaseManager(self.__config.system.database)
    self.__proxy_manager = ProxyManager(self.__config.system.proxies, self.__database_manager)
    self.__selenium_helper = SeleniumHelper(
      self.__config.system,
      self.__config.quick_settings.bot_behavior.default_page_load_timeout,
      self.__proxy_manager
    )
    self.__driver = self.__selenium_helper.get_driver()
    self.__language_parser = LanguageParser()
    self.__indeed_orchestration_engine = IndeedOrchestrationEngine(
      self.__driver,
      self.__selenium_helper,
      self.__database_manager,
      self.__language_parser,
      self.__config.universal,
      self.__config.quick_settings,
      self.__config.indeed
    )
    self.__glassdoor_orchestration_engine = GlassdoorOrchestrationEngine(
      self.__driver,
      self.__selenium_helper,
      self.__database_manager,
      self.__language_parser,
      self.__config.universal,
      self.__config.quick_settings,
      self.__config.glassdoor,
      IndeedApplyNowPage(
        self.__driver,
        self.__selenium_helper,
        self.__config.universal,
        self.__config.quick_settings
      )
    )
    self.__linkedin_orchestration_engine = LinkedinOrchestrationEngine(
      self.__driver,
      self.__selenium_helper,
      self.__database_manager,
      self.__language_parser,
      self.__config.universal,
      self.__config.quick_settings,
      self.__config.linkedin,
      self.__proxy_manager
    )

  def execute(self):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True
    apply_parser = subparsers.add_parser("apply", help="Aggregates jobs; fills out some data; scrapes job info.")
    apply_parser.set_defaults(func=self.apply)
    get_parser = subparsers.add_parser("get", help="Gets scrapped job info.")
    get_parser.add_argument("--ignore-terms", type=int, required=True)
    get_parser.set_defaults(func=self.__get)
    args = parser.parse_args()
    args.func(args)

  def apply(self, args: argparse.Namespace):    # pylint: disable=unused-argument
    try:
      for some_platform in self.__config.quick_settings.bot_behavior.platform_order:
        platform = str(some_platform).lower()
        if platform == Platform.LINKEDIN.value.lower():
          self.__linkedin_orchestration_engine.login()
        elif platform == Platform.GLASSDOOR.value.lower():
          self.__glassdoor_orchestration_engine.login()
        elif platform == Platform.INDEED.value.lower():
          self.__indeed_orchestration_engine.login()
      for some_platform in self.__config.quick_settings.bot_behavior.platform_order:
        platform = str(some_platform).lower()
        if platform == Platform.LINKEDIN.value.lower():
          self.__apply_on_linkedin()
        elif platform == Platform.GLASSDOOR.value.lower():
          self.__apply_on_glassdoor()
        elif platform == Platform.INDEED.value.lower():
          self.__apply_on_indeed()
      input("\n\tPress enter to exit...")
      self.__remove_all_tabs_except_first()
    except Exception:
      traceback.print_exc()
      input("\tPress enter to exit...")
    finally:
      self.__driver.quit()

  def __configure_logger(self):
    def custom_time(record):
      t = time.localtime(record.created)
      return time.strftime("%Y-%m-%d %H:%M:%S", t) + f".{int(record.msecs):03d}"
    logging.basicConfig(
      format='[%(asctime)s] [%(levelname)s] %(message)s',
      datefmt='',
      level=logging.DEBUG
    )
    logging.Formatter.converter = time.localtime
    logging.Formatter.formatTime = lambda self, record, datefmt=None: custom_time(record)
    noisy_loggers = [
      "selenium", "urllib3", "httpx", "asyncio", "trio", "PIL.Image", 
      "undetected_chromedriver", "werkzeug", "hpack", "chardet.charsetprober", 
      "websockets", "chromedriver_autoinstaller"
    ]
    for name in noisy_loggers:
      logging.getLogger(name).setLevel(logging.WARNING)

  def __apply_on_indeed(self) -> None:
    self.__indeed_orchestration_engine.apply()
    if self.__config.quick_settings.bot_behavior.pause_after_each_platform:
      input("\nFinished with Indeed. Press enter to proceed...")
    if self.__config.quick_settings.bot_behavior.remove_tabs_after_each_platform:
      self.__remove_all_tabs_except_first()

  def __apply_on_glassdoor(self) -> None:
    self.__glassdoor_orchestration_engine.apply()
    if self.__config.quick_settings.bot_behavior.pause_after_each_platform:
      input("\nFinished with Glassdoor. Press enter to proceed...")
    if self.__config.quick_settings.bot_behavior.remove_tabs_after_each_platform:
      self.__remove_all_tabs_except_first()

  def __apply_on_linkedin(self) -> None:
    self.__linkedin_orchestration_engine.apply()
    if self.__config.quick_settings.bot_behavior.pause_after_each_platform:
      input("\nFinished with Linkedin. Press enter to proceed...")
    if self.__config.quick_settings.bot_behavior.remove_tabs_after_each_platform:
      self.__remove_all_tabs_except_first()

  def __remove_all_tabs_except_first(self) -> None:
    while len(self.__driver.window_handles) > 1:
      self.__driver.switch_to.window(self.__driver.window_handles[-1])
      self.__driver.close()
    self.__driver.switch_to.window(self.__driver.window_handles[0])

  def __get(self, args: argparse.Namespace) -> None:
    if args.ignore_terms:
      self.__print_highest_ignore_terms(args.ignore_terms)

  def __print_highest_ignore_terms(self, limit: int) -> None:
    print("\n" + "Job Listing Ignore Terms".center(100))
    keywords = self.__database_manager.get_highest_job_listing_ignore_keywords(limit)
    print(f"{"Category":>22}   {"Term":<40} {"Count"}")
    print("─" * 100)
    # Some formatting to ensure all values are in the same format that supports the max count, ex) 1,302 -- 0,021
    max_count = max(x[2] for x in keywords)
    width = len(f"{max_count:,}")
    for category, term, count in keywords:
      print(f"{category:>22}   {term:<40} {count:{width},}")
    print()

Start().execute()
