from selenium.webdriver.remote.webelement import WebElement
from models.enums.element_type import ElementType
from services.misc.selenium_helper import SeleniumHelper


class LinkedinPrivacyPolicyStepper:
  __selenium_helper: SeleniumHelper
  __context_element: WebElement

  def __init__(
    self,
    selenium_helper: SeleniumHelper
  ):
    self.__selenium_helper = selenium_helper

  def set_context(self, context_element: WebElement) -> None:
    self.__context_element = context_element

  def is_present(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Privacy Policy",
      ElementType.H3,
      self.__context_element
    )

  def resolve(self) -> None:
    if self.__is_terms_and_conditions_label():
      self.__handle_terms_and_conditions()

  def __is_terms_and_conditions_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "I Agree Terms & Conditions",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_terms_and_conditions(self) -> None:
    terms_and_conditions_label = self.__selenium_helper.get_element_by_exact_text(
      "I Agree Terms & Conditions",
      ElementType.LABEL,
      self.__context_element
    )
    terms_and_conditions_label.click()
