import logging
import time
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from models.enums.element_type import ElementType
from services.misc.selenium_helper import SeleniumHelper


class IndeedHomePage:
  __selenium_helper: SeleniumHelper

  def __init__(self, selenium_helper: SeleniumHelper):
    self.__selenium_helper = selenium_helper

  def navigate_to_login_page(self) -> None:
    self.__wait_for_security_checkpoint()
    self.__wait_for_sign_in_anchor()
    self.__click_sign_in_anchor()
    self.__wait_for_vague_email_address_label()

  def __wait_for_security_checkpoint(self, timeout=86400.0) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self.__selenium_helper.exact_text_is_present(
        "Additional Verification Required",
        ElementType.H1
      ):
        logging.debug("Waiting for user to resolve security checkpoint...")
        time.sleep(0.5)
      else:
        return

  def __wait_for_sign_in_anchor(self, timeout=3.0) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self.__selenium_helper.exact_text_is_present(
        "Sign in",
        ElementType.ANCHOR
      ):
        return
      logging.debug("Waiting for sign in anchor...")
      time.sleep(0.5)

  def __click_sign_in_anchor(self) -> None:
    while True:
      try:
        sign_in_anchor = self.__selenium_helper.get_element_by_exact_text("Sign in", ElementType.ANCHOR)
        sign_in_anchor.click()
        return
      except NoSuchElementException:
        pass
      except StaleElementReferenceException:
        pass

  def __wait_for_vague_email_address_label(self, timeout=72000.0) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self.__selenium_helper.text_is_present(
        "Email address",
        ElementType.LABEL
      ):
        return
      logging.debug("Waiting for email address label...")
      time.sleep(0.5)
