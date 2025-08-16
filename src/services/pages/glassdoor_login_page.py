import logging
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from models.enums.element_type import ElementType
from models.configs.glassdoor_config import GlassdoorConfig
from services.misc.selenium_helper import SeleniumHelper


class GlassdoorLoginPage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __glassdoor_config: GlassdoorConfig

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    glassdoor_config: GlassdoorConfig
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__glassdoor_config = glassdoor_config

  def login(self) -> None:
    logging.debug("Logging in...")
    self.__wait_for_email_form()
    email_form_name = "emailForm"
    email_form = self.__driver.find_element(By.NAME, email_form_name)
    email_input_id = "inlineUserEmail"
    email_address = self.__glassdoor_config.email
    email_input = email_form.find_element(By.ID, email_input_id)
    self.__selenium_helper.write_to_input(email_address, email_input)
    continue_with_email_span = self.__selenium_helper.get_element_by_exact_text(
      some_text="Continue with email",
      element_type=ElementType.SPAN,
      base_element=email_form
    )
    continue_with_email_button = continue_with_email_span.find_element(By.XPATH, "..")
    continue_with_email_button.click()
    time.sleep(0.2)
    auth_email_form_name = "authEmailForm"
    while True:
      try:
        auth_email_form = self.__driver.find_element(By.NAME, auth_email_form_name)
        break
      except NoSuchElementException:
        logging.debug("Waiting for auth email form to load...")
        time.sleep(0.1)
    password_input_id="inlineUserPassword"
    password = self.__glassdoor_config.password
    password_input = auth_email_form.find_element(By.ID, password_input_id)
    self.__selenium_helper.write_to_input(password, password_input, True)
    time.sleep(0.2)
    sign_in_span_text = "Sign in"
    sign_in_span = self.__selenium_helper.get_element_by_exact_text(
      some_text=sign_in_span_text,
      element_type=ElementType.SPAN,
      base_element=auth_email_form
    )
    sign_in_button = sign_in_span.find_element(By.XPATH, "..")
    while True:
      try:
        sign_in_button.click()
        break
      except ElementClickInterceptedException:
        pass
    expected_landing_url = "https://www.glassdoor.com/Community/index.htm"
    while True:
      try:
        while not expected_landing_url in self.__driver.current_url:
          logging.debug("Waiting for %s to be in url...", expected_landing_url)
          time.sleep(0.5)
        break
      except TimeoutException:
        pass
    WebDriverWait(self.__driver, 20).until(
      lambda d: expected_landing_url in d.current_url
    )
    WebDriverWait(self.__driver, 20).until(
      lambda d: d.execute_script("return document.readyState") == "complete"
    )

  def __wait_for_email_form(self, timeout=10.0) -> None:
    email_form_name = "emailForm"
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        self.__driver.find_element(By.NAME, email_form_name)
        break
      except NoSuchElementException:
        logging.debug("Failed to find email form. Trying again...")
        time.sleep(0.5)
