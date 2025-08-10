from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from models.configs.universal_config import UniversalConfig
from models.enums.element_type import ElementType
from services.misc.selenium_helper import SeleniumHelper


class LinkedinVoluntarySelfIdentificationStepper:
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
      "Voluntary self identification",
      ElementType.H3,
      self.__context_element
    )

  def resolve(self) -> None:
    if self.__is_race_span():
      self.__handle_race_question()
    if self.__is_gender_span():
      self.__handle_gender_question()
    if self.__is_veteran_span():
      self.__handle_veteran_question()
    if self.__is_disability_span():
      self.__handle_disability_question()
    if self.__is_veteran_span_2():
      self.__handle_veteran_question_2()
    if self.__is_name_label():
      self.__handle_name()
    if self.__is_date_input():
      self.__handle_date_input()

  def __is_race_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Race/Ethnicity",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_race_question(self) -> None:
    assert self.__is_race_span()
    hispanic_or_latino_label = self.__selenium_helper.get_element_by_exact_text(
      "Hispanic or Latino",
      ElementType.LABEL,
      self.__context_element
    )
    race_fieldset = hispanic_or_latino_label.find_element(By.XPATH, "../..")
    prefer_not_to_say_label = self.__selenium_helper.get_element_by_exact_text(
      "I prefer not to specify",
      ElementType.LABEL,
      race_fieldset
    )
    prefer_not_to_say_label.click()

  def __is_gender_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Gender",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_gender_question(self) -> None:
    assert self.__is_gender_span()
    male_label = self.__selenium_helper.get_element_by_exact_text(
      "Male",
      ElementType.LABEL,
      self.__context_element
    )
    gender_fieldset = male_label.find_element(By.XPATH, "../..")
    prefer_not_to_say_label = self.__selenium_helper.get_element_by_exact_text(
      "I prefer not to specify",
      ElementType.LABEL,
      gender_fieldset
    )
    prefer_not_to_say_label.click()

  def __is_veteran_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Veteran status",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_veteran_question(self) -> None:
    assert self.__is_veteran_span()
    not_a_veteran_label = self.__selenium_helper.get_element_by_exact_text(
      "I am not a protected veteran",
      ElementType.LABEL,
      self.__context_element
    )
    veteran_fieldset = not_a_veteran_label.find_element(By.XPATH, "../..")
    prefer_not_to_say_label = self.__selenium_helper.get_element_by_exact_text(
      "I prefer not to specify",
      ElementType.LABEL,
      veteran_fieldset
    )
    prefer_not_to_say_label.click()

  def __is_disability_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Disability",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_disability_question(self) -> None:
    assert self.__is_disability_span()
    yes_disability_label = self.__selenium_helper.get_element_by_exact_text(
      "Yes, I have a disability, or have had one in the past",
      ElementType.LABEL,
      self.__context_element
    )
    disability_fieldset = yes_disability_label.find_element(By.XPATH, "../..")
    prefer_not_to_say_label = self.__selenium_helper.get_element_by_exact_text(
      "I do not want to answer",
      ElementType.LABEL,
      disability_fieldset
    )
    prefer_not_to_say_label.click()

  def __is_veteran_span_2(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Are you a veteran?",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_veteran_question_2(self) -> None:
    assert self.__is_veteran_span_2()
    is_veteran = self.__universal_config.about_me.military_veteran
    veteran_span = self.__selenium_helper.get_element_by_exact_text(
      "Are you a veteran?",
      ElementType.SPAN,
      self.__context_element
    )
    veteran_fieldset = veteran_span.find_element(By.XPATH, "../../..")
    if is_veteran:
      is_veteran_label = self.__selenium_helper.get_element_by_exact_text(
        "Yes",
        ElementType.LABEL,
        veteran_fieldset
      )
      is_veteran_label.click()
    else:
      is_not_veteran_label = self.__selenium_helper.get_element_by_exact_text(
        "No",
        ElementType.LABEL,
        veteran_fieldset
      )
      is_not_veteran_label.click()

  def __is_name_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Your Name",
      ElementType.LABEL
    )

  def __handle_name(self) -> None:
    assert self.__is_name_label()
    first_name = self.__universal_config.about_me.name.first
    last_name = self.__universal_config.about_me.name.last
    full_name = f"{first_name} {last_name}"
    name_label = self.__selenium_helper.get_element_by_exact_text(
      "Your Name",
      ElementType.LABEL
    )
    name_input = name_label.find_element(By.XPATH, "../input")
    self.__selenium_helper.write_to_input(full_name, name_input)

  def __is_date_input(self) -> bool:
    date_input_name = "artdeco-date"
    try:
      self.__context_element.find_element(By.NAME, date_input_name)
      return True
    except NoSuchElementException:
      return False

  def __handle_date_input(self) -> None:
    assert self.__is_date_input()
    mmddyyy_date = datetime.today().strftime('%m/%d/%Y')
    date_input_name = "artdeco-date"
    date_input = self.__context_element.find_element(By.NAME, date_input_name)
    self.__selenium_helper.write_to_input(mmddyyy_date, date_input)
