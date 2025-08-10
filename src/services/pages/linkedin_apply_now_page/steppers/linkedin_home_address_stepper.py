from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from models.enums.element_type import ElementType
from models.configs.universal_config import UniversalConfig
from services.misc.selenium_helper import SeleniumHelper


class LinkedinHomeAddressStepper:
  __selenium_helper: SeleniumHelper
  __universal_config: UniversalConfig
  __context_element: WebElement

  def __init__(
    self,
    selenium_helper: SeleniumHelper,
    universal_config: UniversalConfig
  ):
    self.__selenium_helper = selenium_helper
    self.__universal_config = universal_config

  def set_context(self, context_element: WebElement) -> None:
    self.__context_element = context_element

  def is_present(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Home address",
      ElementType.H3,
      self.__context_element
    )
  def resolve(self) -> None:
    if self.__is_street_address_label():
      self.__handle_street_address()
    if self.__is_city_span():
      self.__handle_city()
    if self.__is_zip_slash_postal_code_label():
      self.__handle_zip_slash_postal_code()
    if self.__is_state_label():
      self.__handle_state()
    self.__remove_suggestion_dialogs()

  def __is_street_address_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Street address line 1",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_street_address(self) -> None:
    assert self.__is_street_address_label()
    street_address = self.__universal_config.about_me.location.street_address
    street_address_line_one_label = self.__selenium_helper.get_element_by_exact_text(
      "Street address line 1",
      ElementType.LABEL,
      self.__context_element
    )
    street_address_line_one_input_id = street_address_line_one_label.get_attribute("for")
    street_address_line_one_input = self.__context_element.find_element(By.ID, street_address_line_one_input_id)
    self.__selenium_helper.write_to_input(street_address, street_address_line_one_input)

  def __is_city_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "City",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_city(self) -> None:
    assert self.__is_city_span()
    # For some silly reason Linkedin wants "city" in this format
    city = f"{self.__universal_config.about_me.location.city}, {self.__universal_config.about_me.location.state}, {self.__universal_config.about_me.location.country}"    # pylint: disable=line-too-long
    city_span = self.__selenium_helper.get_element_by_exact_text("City", ElementType.SPAN, self.__context_element)
    city_label = city_span.find_element(By.XPATH, "..")
    city_input_id = city_label.get_attribute("for")
    city_input = self.__context_element.find_element(By.ID, city_input_id)
    self.__selenium_helper.write_to_input(city, city_input)
    while str(city_input.get_attribute("aria-expanded")).lower().strip() == "true":
      city_input.send_keys(Keys.TAB)

  def __is_zip_slash_postal_code_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Zip / Postal Code",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_zip_slash_postal_code(self) -> None:
    assert self.__is_zip_slash_postal_code_label()
    postal_code = self.__universal_config.about_me.location.postal_code
    postal_code_label = self.__selenium_helper.get_element_by_exact_text(
      "ZIP / Postal Code",
      ElementType.LABEL,
      self.__context_element
    )
    postal_code_input_id = postal_code_label.get_attribute("for")
    postal_code_input = self.__context_element.find_element(By.ID, postal_code_input_id)
    self.__selenium_helper.write_to_input(str(postal_code), postal_code_input)

  def __is_state_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "State",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_state(self) -> None:
    assert self.__is_state_label()
    state = self.__universal_config.about_me.location.state
    state_label = self.__selenium_helper.get_element_by_exact_text(
      "State",
      ElementType.LABEL,
      self.__context_element
    )
    state_input_id = state_label.get_attribute("for")
    state_input = self.__context_element.find_element(By.ID, state_input_id)
    self.__selenium_helper.write_to_input(state, state_input)

  def __remove_suggestion_dialogs(self) -> None:
    self.__context_element.click()
