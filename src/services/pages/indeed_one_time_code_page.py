import logging
import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from models.configs.indeed_config import IndeedConfig
from models.enums.element_type import ElementType
from services.misc.email_handler import EmailHandler
from services.misc.selenium_helper import SeleniumHelper


class IndeedOneTimeCodePage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __indeed_config: IndeedConfig
  __email_handler: EmailHandler

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    indeed_config: IndeedConfig
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__indeed_config = indeed_config
    self.__email_handler = EmailHandler()

  def is_present(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Check your email for a code",
      ElementType.H1
    )

  def can_resolve_with_mail_dot_com(self) -> bool:
    EMAIL = os.getenv("MAIL_DOT_COM_EMAIL")
    PASSWORD = os.getenv("MAIL_DOT_COM_PASS")
    MAIL_DOT_COM_IN_EMAIL_ADDRESS = "@mail.com" in self.__indeed_config.email
    if MAIL_DOT_COM_IN_EMAIL_ADDRESS and EMAIL and PASSWORD:
      return True
    return False

  def resolve_with_mail_dot_com(self) -> None:
    assert self.can_resolve_with_mail_dot_com()
    while True:
      try:
        code = self.__email_handler.get_indeed_one_time_code_from_mdc()
        break
      except TimeoutError:
        send_new_code_span = self.__selenium_helper.get_element_by_exact_text(
          "Send new code",
          ElementType.SPAN
        )
        send_new_code_span.click()
        time.sleep(1)
      except AssertionError:
        logging.warning("Failed to get one time code. Trying again...")
        time.sleep(0.1)
    self.__wait_for_one_time_code_label()
    self.__enter_one_time_code(code)

  def wait_for_captcha_resolution(self) -> None:
    captcha_url = "secure.indeed.com"
    while captcha_url in self.__driver.current_url:
      logging.debug("Waiting for captcha resolution...")
      time.sleep(0.5)

  def __wait_for_one_time_code_label(self, timeout=10.0) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self.__selenium_helper.text_is_present(
        "Enter code",
        ElementType.LABEL
      ):
        return
      logging.debug("Waiting for one-time code label...")
      time.sleep(0.5)

  def __enter_one_time_code(self, code: str) -> None:
    enter_code_label = self.__selenium_helper.get_element_by_text(
      "Enter code",
      ElementType.LABEL
    )
    enter_code_input = enter_code_label.find_element(By.XPATH, "../span/input")
    self.__selenium_helper.write_to_input(code, enter_code_input)
