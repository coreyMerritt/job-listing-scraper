from abc import ABC, abstractmethod
import undetected_chromedriver as uc
from models.configs.universal_config import UniversalConfig
from services.misc.selenium_helper import SeleniumHelper


class OrchestrationEngine(ABC):
  _driver: uc.Chrome
  _selenium_helper: SeleniumHelper
  _universal_config: UniversalConfig

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    universal_config: UniversalConfig
  ):
    self._driver = driver
    self._selenium_helper = selenium_helper
    self._universal_config = universal_config

  @abstractmethod
  def login(self) -> None:
    pass

  def apply_from_single_listing_page(self) -> None:
    pass
