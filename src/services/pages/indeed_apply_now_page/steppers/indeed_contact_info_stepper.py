import logging
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from models.enums.element_type import ElementType
from models.configs.universal_config import UniversalConfig
from services.misc.selenium_helper import SeleniumHelper


class IndeedContactInfoStepper:
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
    CONTACT_INFO_URL = "smartapply.indeed.com/beta/indeedapply/form/contact-info"
    return CONTACT_INFO_URL in self.__driver.current_url

  def resolve(self) -> None:
    self.__handle_phone_number_input()
    try:    # Sometimes this input isnt in the form -- seemingly when accessed from glassdoor specifically
      self.__handle_city_state_input()
    except NoSuchElementException:
      pass
    self.__handle_last_name_input()
    self.__handle_first_name_input()

  def __handle_phone_number_input(self) -> None:
    phone_number = self.__universal_config.about_me.contact.phone_number
    potential_phone_number_input_names = [
      "phone",
      "phoneNumber"
    ]
    for name in potential_phone_number_input_names:
      try:
        phone_number_input = self.__driver.find_element(By.NAME, name)
        self.__selenium_helper.write_to_input(phone_number, phone_number_input)
        return
      except NoSuchElementException:
        pass
    raise NoSuchElementException("Failed to find phone number input.")

  def __handle_last_name_input(self) -> None:
    last_name = self.__universal_config.about_me.name.last
    potential_last_name_input_names = [
      "names-last-name",
      "lastName"
    ]
    for name in potential_last_name_input_names:
      try:
        last_name_input = self.__driver.find_element(By.NAME, name)
        self.__selenium_helper.write_to_input(last_name, last_name_input)
        return
      except NoSuchElementException:
        pass
    raise NoSuchElementException("Failed to find last name input.")

  def __handle_first_name_input(self) -> None:
    first_name = self.__universal_config.about_me.name.first
    potential_first_name_input_names = [
      "names-first-name",
      "firstName"
    ]
    for name in potential_first_name_input_names:
      try:
        first_name_input = self.__driver.find_element(By.NAME, name)
        self.__selenium_helper.write_to_input(first_name, first_name_input)
        return
      except NoSuchElementException:
        pass
    raise NoSuchElementException("Failed to find first name input.")

  def __handle_city_state_input(self) -> None:
    city = self.__universal_config.about_me.location.city
    state_code = self.__universal_config.about_me.location.state_code
    city_state = f"{city}, {state_code}"
    potential_city_state_input_names = [
      "location-locality",
      "location.city"
    ]
    for name in potential_city_state_input_names:
      try:
        city_state_input = self.__driver.find_element(By.NAME, name)
        self.__selenium_helper.write_to_input(city_state, city_state_input)
        return
      except NoSuchElementException:
        pass
    raise NoSuchElementException("Failed to find city-state input.")
