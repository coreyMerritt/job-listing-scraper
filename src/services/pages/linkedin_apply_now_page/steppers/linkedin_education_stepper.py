import logging
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from models.configs.universal_config import Date, UniversalConfig
from models.enums.element_type import ElementType
from services.misc.selenium_helper import SeleniumHelper


class LinkedinEducationStepper:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __universal_config: UniversalConfig
  __context_element: WebElement

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    universal_config: UniversalConfig
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__universal_config = universal_config

  def set_context(self, context_element: WebElement) -> None:
    self.__context_element = context_element

  def is_present(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Education",
      ElementType.SPAN,
      self.__context_element
    )

  def resolve(self) -> None:
    self.__remove_all_education()
    self.__add_all_education()

  def __remove_all_education(self) -> None:
    while True:
      if not self.__is_education():
        break
      self.__remove_top_education()
      time.sleep(0.1)

  def __is_education(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Remove",
      ElementType.SPAN,
      self.__context_element
    )

  def __remove_top_education(self) -> None:
    top_education_remove_span = self.__selenium_helper.get_element_by_exact_text(
      "Remove",
      ElementType.SPAN,
      self.__context_element
    )
    top_education_remove_button = top_education_remove_span.find_element(By.XPATH, "..")
    top_education_remove_button.click()
    self.__wait_for_removal_confirmation_div()
    self.__confirm_removal()

  def __wait_for_removal_confirmation_div(self, timeout=10) -> None:
    confirm_removal_div_xpath = "/html/body/div[4]/div[2]/div"
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        self.__driver.find_element(By.XPATH, confirm_removal_div_xpath)
        return
      except NoSuchElementException:
        logging.debug("Failed to find removal confirmation div. Trying again...")
        time.sleep(0.1)
    raise NoSuchElementException("Failed waiting for removal confirmation div.")

  def __confirm_removal(self) -> None:
    self.__wait_for_removal_confirmation_div()
    confirm_removal_div_xpath = "/html/body/div[4]/div[2]/div"
    confirm_removal_div = self.__driver.find_element(By.XPATH, confirm_removal_div_xpath)
    remove_span = self.__selenium_helper.get_element_by_exact_text(
      "Remove",
      ElementType.SPAN,
      confirm_removal_div
    )
    remove_button = remove_span.find_element(By.XPATH, "..")
    remove_button.click()

  def __add_all_education(self) -> None:
    degrees = self.__universal_config.about_me.education.degrees
    for degree in degrees:
      city = f"{degree.city}, {degree.state}, {degree.country}"
      add_more_span = self.__selenium_helper.get_element_by_exact_text(
        "Add more",
        ElementType.SPAN,
        self.__context_element
      )
      add_more_button = add_more_span.find_element(By.XPATH, "..")
      add_more_button.click()
      if self.__is_input_based_stepper():
        if self.__is_school_label():
          self.__add_school_by_label(degree.school)
        if self.__is_city_span():
          self.__add_city(city)
        if self.__is_degree_type_label():
          self.__add_degree_type_by_label(degree.degree_type)
        if self.__is_field_of_study_label():
          self.__add_field_of_study_by_label(degree.field_of_study)
        if self.__is_currently_attending_label():
          if degree.currently_attending:
            self.__click_currently_attending()
        if self.__is_start_time_fieldset():
          self.__add_start_time(degree.start)
        if self.__is_end_time_fieldset():
          if not degree.currently_attending:
            self.__add_end_time(degree.end)
      else:
        if self.__is_currently_attending_label():
          if degree.currently_attending:
            self.__click_currently_attending()
        if self.__is_start_time_fieldset_alt():
          self.__add_start_time_alt(degree.start)
        if self.__is_end_time_fieldset_alt():
          if not degree.currently_attending:
            self.__add_end_time_alt(degree.end)
        if self.__is_school_span():
          self.__add_school_by_span(degree.school)
        if self.__is_degree_type_span():
          self.__add_degree_type_by_span(degree.degree_type)
        if self.__is_field_of_study_span():
          self.__add_field_of_study_by_span(degree.field_of_study)
      self.__save()

  def __is_input_based_stepper(self) -> bool:
    return self.__is_school_label()

  def __is_school_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "School",
      ElementType.LABEL,
      self.__context_element
    )

  def __add_school_by_label(self, school: str) -> None:
    assert self.__is_school_label()
    school_label = self.__selenium_helper.get_element_by_exact_text(
      "School",
      ElementType.LABEL,
      self.__context_element
    )
    school_input = school_label.find_element(By.XPATH, "../input")
    self.__selenium_helper.write_to_input(school, school_input)

  def __is_city_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "City",
      ElementType.SPAN,
      self.__context_element
    )

  def __add_city(self, city: str) -> None:
    assert self.__is_city_span()
    city_span = self.__selenium_helper.get_element_by_exact_text(
      "City",
      ElementType.SPAN,
      self.__context_element
    )
    city_input = city_span.find_element(By.XPATH, "../../div/input")
    self.__selenium_helper.write_to_input(city, city_input)
    while str(city_input.get_attribute("aria-expanded")).lower().strip() == "true":
      city_input.send_keys(Keys.TAB)

  def __is_degree_type_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Degree",
      ElementType.LABEL,
      self.__context_element
    )

  def __add_degree_type_by_label(self, degree_type: str) -> None:
    assert self.__is_degree_type_label()
    degree_label = self.__selenium_helper.get_element_by_exact_text(
      "Degree",
      ElementType.LABEL,
      self.__context_element
    )
    if self.__is_degree_type_input(degree_label):
      self.__add_degree_type_via_input(degree_label, degree_type)
    elif self.__is_degree_type_select(degree_label):
      self.__add_degree_type_via_select(degree_label, degree_type)

  def __is_degree_type_input(self, degree_label: WebElement) -> bool:
    try:
      degree_label.find_element(By.XPATH, "../input")
      return True
    except NoSuchElementException:
      return False

  def __is_degree_type_select(self, degree_label: WebElement) -> bool:
    try:
      degree_label.find_element(By.XPATH, "../select")
      return True
    except NoSuchElementException:
      return False

  def __add_degree_type_via_input(self, degree_label: WebElement, degree_type: str) -> None:
    assert self.__is_degree_type_input(degree_label)
    degree_input = degree_label.find_element(By.XPATH, "../input")
    self.__selenium_helper.write_to_input(degree_type, degree_input)

  def __add_degree_type_via_select(self, degree_label: WebElement, degree_type: str) -> None:
    assert self.__is_degree_type_select(degree_label)
    degree_select = Select(degree_label.find_element(By.XPATH, "../select"))
    try:
      degree_select.select_by_value(degree_type)
    except NoSuchElementException:
      degree_select.select_by_value("Other")

  def __is_field_of_study_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Major / Field of study",
      ElementType.LABEL,
      self.__context_element
    )

  def __add_field_of_study_by_label(self, field_of_study: str) -> None:
    assert self.__is_field_of_study_label()
    field_of_study_label = self.__selenium_helper.get_element_by_exact_text(
      "Major / Field of study",
      ElementType.LABEL,
      self.__context_element
    )
    field_of_study_input = field_of_study_label.find_element(By.XPATH, "../input")
    self.__selenium_helper.write_to_input(field_of_study, field_of_study_input)

  def __is_currently_attending_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "I currently attend this institution",
      ElementType.LABEL,
      self.__context_element
    )

  def __click_currently_attending(self) -> None:
    assert self.__is_currently_attending_label()
    currently_attending_label = self.__selenium_helper.get_element_by_exact_text(
      "I currently attend this institution",
      ElementType.LABEL,
      self.__context_element
    )
    currently_attending_label.click()

  def __is_start_time_fieldset(self) -> bool:
    relative_start_time_fieldset_xpath = "./div[2]/div/div[2]/form/div[1]/div/div[1]/div[5]/div[2]/div/div[1]/fieldset[1]"    # pylint: disable=line-too-long
    try:
      self.__context_element.find_element(By.XPATH, relative_start_time_fieldset_xpath)
      return True
    except NoSuchElementException:
      return False

  def __add_start_time(self, start: Date) -> None:
    assert self.__is_start_time_fieldset()
    relative_start_time_fieldset_xpath = "./div[2]/div/div[2]/form/div[1]/div/div[1]/div[5]/div[2]/div/div[1]/fieldset[1]"     # pylint: disable=line-too-long
    start_time_fieldset = self.__context_element.find_element(By.XPATH, relative_start_time_fieldset_xpath)
    relative_start_month_select_xpath = "./div/span[1]/select"
    start_month_select = Select(start_time_fieldset.find_element(By.XPATH, relative_start_month_select_xpath))
    start_month_select.select_by_index(start.month)
    relative_start_year_select_xpath = "./div/span[2]/select"
    start_year_select = Select(start_time_fieldset.find_element(By.XPATH, relative_start_year_select_xpath))
    start_year_select.select_by_value(str(start.year))

  def __is_end_time_fieldset(self) -> bool:
    relative_end_time_fieldset_xpath = "./div[2]/div/div[2]/form/div[1]/div/div[1]/div[5]/div[2]/div/div[1]/fieldset[2]"
    try:
      self.__context_element.find_element(By.XPATH, relative_end_time_fieldset_xpath)
      return True
    except NoSuchElementException:
      return False

  def __add_end_time(self, end: Date) -> None:
    assert self.__is_end_time_fieldset()
    relative_end_time_fieldset_xpath = "./div[2]/div/div[2]/form/div[1]/div/div[1]/div[5]/div[2]/div/div[1]/fieldset[2]"
    end_time_fieldset = self.__context_element.find_element(By.XPATH, relative_end_time_fieldset_xpath)
    relative_end_month_select_xpath = "./div/span[1]/select"
    end_month_select = Select(end_time_fieldset.find_element(By.XPATH, relative_end_month_select_xpath))
    end_month_select.select_by_index(end.month)
    relative_end_year_select_xpath = "./div/span[2]/select"
    end_year_select = Select(end_time_fieldset.find_element(By.XPATH, relative_end_year_select_xpath))
    end_year_select.select_by_value(str(end.year))

  def __is_start_time_fieldset_alt(self) -> bool:
    relative_start_time_fieldset_xpath = "./div[2]/div/div[2]/form/div[1]/div/div[1]/div[1]/div[2]/div/div[1]/fieldset[1]"    # pylint: disable=line-too-long
    try:
      self.__context_element.find_element(By.XPATH, relative_start_time_fieldset_xpath)
      return True
    except NoSuchElementException:
      return False

  def __add_start_time_alt(self, start: Date) -> None:
    assert self.__is_start_time_fieldset_alt()
    relative_start_time_fieldset_xpath = "./div[2]/div/div[2]/form/div[1]/div/div[1]/div[1]/div[2]/div/div[1]/fieldset[1]"     # pylint: disable=line-too-long
    start_time_fieldset = self.__context_element.find_element(By.XPATH, relative_start_time_fieldset_xpath)
    relative_start_month_select_xpath = "./div/span[1]/select"
    start_month_select = Select(start_time_fieldset.find_element(By.XPATH, relative_start_month_select_xpath))
    start_month_select.select_by_index(start.month)
    relative_start_year_select_xpath = "./div/span[2]/select"
    start_year_select = Select(start_time_fieldset.find_element(By.XPATH, relative_start_year_select_xpath))
    start_year_select.select_by_value(str(start.year))

  def __is_end_time_fieldset_alt(self) -> bool:
    relative_end_time_fieldset_xpath = "./div[2]/div/div[2]/form/div[1]/div/div[1]/div[1]/div[2]/div/div[1]/fieldset[2]"
    try:
      self.__context_element.find_element(By.XPATH, relative_end_time_fieldset_xpath)
      return True
    except NoSuchElementException:
      return False

  def __add_end_time_alt(self, end: Date) -> None:
    assert self.__is_end_time_fieldset_alt()
    relative_end_time_fieldset_xpath = "./div[2]/div/div[2]/form/div[1]/div/div[1]/div[1]/div[2]/div/div[1]/fieldset[2]"
    end_time_fieldset = self.__context_element.find_element(By.XPATH, relative_end_time_fieldset_xpath)
    relative_end_month_select_xpath = "./div/span[1]/select"
    end_month_select = Select(end_time_fieldset.find_element(By.XPATH, relative_end_month_select_xpath))
    end_month_select.select_by_index(end.month)
    relative_end_year_select_xpath = "./div/span[2]/select"
    end_year_select = Select(end_time_fieldset.find_element(By.XPATH, relative_end_year_select_xpath))
    end_year_select.select_by_value(str(end.year))


  def __is_school_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "School",
      ElementType.SPAN,
      self.__context_element
    )

  def __add_school_by_span(self, school: str) -> None:
    assert self.__is_school_span()
    school_span = self.__selenium_helper.get_element_by_exact_text(
      "School",
      ElementType.SPAN,
      self.__context_element
    )
    school_select = school_span.find_element(By.XPATH, "../../select")
    self.__selenium_helper.write_to_select(school, school_select)

  def __is_degree_type_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Degree",
      ElementType.SPAN,
      self.__context_element
    )

  def __add_degree_type_by_span(self, degree_type: str) -> None:
    assert self.__is_degree_type_span()
    degree_type_span = self.__selenium_helper.get_element_by_exact_text(
      "Degree",
      ElementType.SPAN,
      self.__context_element
    )
    degree_type_select = degree_type_span.find_element(By.XPATH, "../../select")
    self.__selenium_helper.write_to_select(degree_type, degree_type_select)

  def __is_field_of_study_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Discipline",
      ElementType.SPAN,
      self.__context_element
    )

  def __add_field_of_study_by_span(self, field_of_study: str) -> None:
    assert self.__is_field_of_study_span()
    field_of_study_span = self.__selenium_helper.get_element_by_exact_text(
      "Discipline",
      ElementType.SPAN,
      self.__context_element
    )
    field_of_study_select = field_of_study_span.find_element(By.XPATH, "../../select")
    self.__selenium_helper.write_to_select(field_of_study, field_of_study_select)

  def __save(self) -> None:
    save_span = self.__selenium_helper.get_element_by_exact_text(
      "Save",
      ElementType.SPAN,
      self.__context_element
    )
    save_button = save_span.find_element(By.XPATH, "..")
    save_button.click()
