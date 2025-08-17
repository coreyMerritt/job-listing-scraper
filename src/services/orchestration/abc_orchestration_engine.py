from abc import ABC, abstractmethod
import undetected_chromedriver as uc
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from services.misc.selenium_helper import SeleniumHelper


class OrchestrationEngine(ABC):
  _driver: uc.Chrome
  _selenium_helper: SeleniumHelper
  _universal_config: UniversalConfig
  _quick_settings: QuickSettings

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

  @abstractmethod
  def login(self) -> None:
    pass

  @abstractmethod
  def scrape(self) -> None:
    pass

  @abstractmethod
  def get_jobs_parsed_count(self) -> int:
    pass

  @abstractmethod
  def reset_jobs_parsed_count(self) -> None:
    pass
