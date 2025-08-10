import logging
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import JavascriptException, NoSuchElementException
from models.configs.linkedin_config import LinkedinConfig
from services.misc.selenium_helper import SeleniumHelper


class LinkedinLoginPage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __linkedin_config: LinkedinConfig

  def __init__(self, driver: uc.Chrome, selenium_helper: SeleniumHelper, linkedin_config: LinkedinConfig):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__linkedin_config = linkedin_config

  def login(self) -> None:
    logging.debug("Logging in...")
    self.__driver.get("https://linkedin.com/login")
    email_address = self.__linkedin_config.email
    email_address_input_id = "username"
    email_address_input = self.__driver.find_element(By.ID, email_address_input_id)
    self.__selenium_helper.write_to_input(email_address, email_address_input)
    password = self.__linkedin_config.password
    password_input_id = "password"
    password_input = self.__driver.find_element(By.ID, password_input_id)
    self.__selenium_helper.write_to_input(password, password_input, True)
    try:
      self.__selenium_helper.check_box_by_name('rememberMeOptIn', False)
    except JavascriptException:
      pass    # No "remember me" textbox was generated
    except NoSuchElementException:
      pass    # No "remember me" textbox was generated
    sign_in_button_selector = ".btn__primary--large.from__button--floating"
    sign_in_button = self.__driver.find_element(By.CSS_SELECTOR, sign_in_button_selector)
    sign_in_button.click()
    while (
      'https://www.linkedin.com/checkpoint/challenge' in self.__driver.current_url
      or 'https://www.linkedin.com/login' in self.__driver.current_url
    ):
      logging.debug('Waiting for user to resolve security checkpoint...')
      time.sleep(0.5)
