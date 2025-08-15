#!/usr/bin/env python3

import argparse
from functools import partial
import logging
import time
import traceback
import yaml
import undetected_chromedriver as uc
from dacite import from_dict
from exceptions.memory_overload_exception import MemoryOverloadException
from exceptions.rate_limited_exception import RateLimitedException
from models.configs.full_config import FullConfig
from models.enums.platform import Platform
from services.misc.database_manager import DatabaseManager
from services.misc.proxy_manager import ProxyManager
from services.misc.selenium_helper import SeleniumHelper
from services.orchestration.glassdoor_orchestration_engine import GlassdoorOrchestrationEngine
from services.orchestration.indeed_orchestration_engine import IndeedOrchestrationEngine
from services.orchestration.linkedin_orchestration_engine import LinkedinOrchestrationEngine
from services.misc.language_parser import LanguageParser


def start() -> None:
  configure_logger()
  with open("config.yml", "r", encoding='utf-8') as config_file:
    raw_config = yaml.safe_load(config_file)
  config = from_dict(data_class=FullConfig, data=raw_config)
  parse_args(config)
  database_manager = DatabaseManager(config.system.database)
  proxy_manager = ProxyManager(config.system.proxies, database_manager)
  selenium_helper = SeleniumHelper(
    config.system,
    config.quick_settings.bot_behavior.default_page_load_timeout,
    proxy_manager
  )
  driver = selenium_helper.get_driver()
  language_parser = LanguageParser()
  indeed_orchestration_engine = IndeedOrchestrationEngine(
    driver,
    selenium_helper,
    config.universal,
    config.quick_settings,
    config.indeed,
    database_manager,
    language_parser,
    proxy_manager
  )
  glassdoor_orchestration_engine = GlassdoorOrchestrationEngine(
    driver,
    selenium_helper,
    database_manager,
    language_parser,
    proxy_manager,
    config.universal,
    config.quick_settings,
    config.glassdoor
  )
  linkedin_orchestration_engine = LinkedinOrchestrationEngine(
    driver,
    selenium_helper,
    database_manager,
    language_parser,
    config.universal,
    config.quick_settings,
    config.linkedin,
    proxy_manager
  )
  scrape(
    config,
    glassdoor_orchestration_engine,
    indeed_orchestration_engine,
    linkedin_orchestration_engine,
    proxy_manager,
    driver
  )

def parse_args(config: FullConfig) -> None:
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest="command")
  subparsers.required = False
  parser.set_defaults(func=lambda args: None)
  glassdoor_parser = subparsers.add_parser("glassdoor")
  glassdoor_parser.set_defaults(func=partial(glassdoor, config))
  indeed_parser = subparsers.add_parser("indeed")
  indeed_parser.set_defaults(func=partial(indeed, config))
  linkedin_parser = subparsers.add_parser("linkedin")
  linkedin_parser.set_defaults(func=partial(linkedin, config))
  all_parser = subparsers.add_parser("all")
  all_parser.set_defaults(func=partial(all_platforms, config))
  args = parser.parse_args()
  args.func(args)

def scrape(
  config: FullConfig,
  glassdoor_orchestration_engine: GlassdoorOrchestrationEngine,
  indeed_orchestration_engine: IndeedOrchestrationEngine,
  linkedin_orchestration_engine: LinkedinOrchestrationEngine,
  proxy_manager: ProxyManager,
  driver: uc.Chrome
) -> None:
  for some_platform in config.quick_settings.bot_behavior.platform_order:
    platform = str(some_platform).lower()
    if platform == Platform.GLASSDOOR.value.lower():
      glassdoor_orchestration_engine.login()
    elif platform == Platform.INDEED.value.lower():
      indeed_orchestration_engine.login()
    elif platform == Platform.LINKEDIN.value.lower():
      linkedin_orchestration_engine.login()
    while True:
      try:
        if platform == Platform.GLASSDOOR.value.lower():
          glassdoor_orchestration_engine.scrape()
        elif platform == Platform.INDEED.value.lower():
          indeed_orchestration_engine.scrape()
        elif platform == Platform.LINKEDIN.value.lower():
          linkedin_orchestration_engine.scrape()
      except MemoryOverloadException as e:
        raise e
      except RateLimitedException as e:
        proxy_manager.log_rate_limit_block(e.get_platform())
        raise e
      except Exception:
        traceback.print_exc()
        input("\tPress enter to exit...")
      finally:
        driver.quit()

def glassdoor(config: FullConfig, args: argparse.Namespace) -> None:    # pylint: disable=unused-argument
  config.quick_settings.bot_behavior.platform_order = [Platform.GLASSDOOR.value]

def indeed(config: FullConfig, args: argparse.Namespace) -> None:    # pylint: disable=unused-argument
  config.quick_settings.bot_behavior.platform_order = [Platform.INDEED.value]

def linkedin(config: FullConfig, args: argparse.Namespace) -> None:    # pylint: disable=unused-argument
  config.quick_settings.bot_behavior.platform_order = [Platform.LINKEDIN.value]

def all_platforms(config: FullConfig, args: argparse.Namespace) -> None:    # pylint: disable=unused-argument
  config.quick_settings.bot_behavior.platform_order = [
    Platform.GLASSDOOR.value,
    Platform.INDEED.value,
    Platform.LINKEDIN.value
  ]

def configure_logger():
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


while True:
  try:
    start()
  except MemoryOverloadException:
    print("\nCurrent memory usage is too high. Please clean up existing tabs to continue safely.")
    input("\tPress enter to proceed...")
  except RateLimitedException as e:
    input("Rate limiting has been logged in db. Press Enter restart the system...")
