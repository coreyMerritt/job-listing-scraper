import logging
import time
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException
from models.configs.universal_config import UniversalConfig
from models.enums.element_type import ElementType
from services.misc.selenium_helper import SeleniumHelper


class IndeedResumeStepper:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __universal_config: UniversalConfig

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    universal_config: UniversalConfig
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__universal_config = universal_config

  def is_present(self) -> bool:
    RESUME_URL = "smartapply.indeed.com/beta/indeedapply/form/resume"
    EXCLUSION_URL_1 = "relevant-experience"
    EXCLUSION_URL_2 = "additional-documents"
    return (
      RESUME_URL in self.__driver.current_url
      and EXCLUSION_URL_1 not in self.__driver.current_url
      and EXCLUSION_URL_2 not in self.__driver.current_url
    )

  def resolve(self) -> None:
    if not self.__resume_preview_is_visible():
      self.__select_first_resume_with_name()

  def __resume_preview_is_visible(self) -> bool:
    return self.__selenium_helper.exact_text_is_present("Resume options", ElementType.SPAN)

  def __select_first_resume_with_name(self, timeout=5) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      if not self.is_present():
        return
      try:
        first = self.__universal_config.about_me.name.first
        last = self.__universal_config.about_me.name.last
        expected_resume_name = f"{first}-{last}.pdf"
        resume_span = self.__selenium_helper.get_element_by_exact_text(
          expected_resume_name,
          ElementType.SPAN
        )
        resume_span.click()
        return
      except NoSuchElementException:
        logging.debug("Failed to click resume span. Trying again...")
        time.sleep(0.5)
    raise NoSuchElementException("Failed to click resume span.")
