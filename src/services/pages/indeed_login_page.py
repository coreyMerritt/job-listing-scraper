import logging
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from models.configs.indeed_config import IndeedConfig
from models.enums.element_type import ElementType
from services.misc.selenium_helper import SeleniumHelper


class IndeedLoginPage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __indeed_config: IndeedConfig

  def __init__(self, driver: uc.Chrome, selenium_helper: SeleniumHelper, indeed_config: IndeedConfig):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__indeed_config = indeed_config

  def login(self) -> None:
    base_url = "https://www.indeed.com"
    logging.debug("Logging into %s...", base_url)
    self.__driver.get(base_url)
    self.__wait_for_security_checkpoint()
    self.__wait_for_sign_in_anchor()
    self.__click_sign_in_anchor()
    self.__wait_for_vague_email_address_label()
    self.__write_email_to_vague_input()
    self.__click_continue_button()

  def __wait_for_security_checkpoint(self, timeout=86400) -> None:
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

  def __wait_for_sign_in_anchor(self, timeout=3) -> None:
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
        sign_in_url = sign_in_anchor.get_attribute("href")
        assert sign_in_url
        self.__driver.get(sign_in_url)
        return
      except NoSuchElementException:
        pass
      except StaleElementReferenceException:
        pass

  def __wait_for_vague_email_address_label(self, timeout=9999) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self.__selenium_helper.text_is_present(
        "Email address",
        ElementType.LABEL
      ):
        return
      logging.debug("Waiting for email address label...")
      time.sleep(0.5)

  def __write_email_to_vague_input(self) -> None:
    email_address = self.__indeed_config.email
    email_address_label = self.__selenium_helper.get_element_by_text(
      "Email address",
      ElementType.LABEL
    )
    email_address_input = email_address_label.find_element(By.XPATH, "../span/input")
    self.__selenium_helper.write_to_input(email_address, email_address_input)

  def __click_continue_button(self) -> None:
    continue_button_xpath = "/html/body/div/div[2]/main/div/div/div[2]/div/form/button"
    continue_button = self.__driver.find_element(By.XPATH, continue_button_xpath)
    continue_button.click()
