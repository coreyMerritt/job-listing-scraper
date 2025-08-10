import logging
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException
from models.configs.universal_config import Date, UniversalConfig
from models.enums.element_type import ElementType
from services.misc.selenium_helper import SeleniumHelper


class LinkedinWorkExperienceStepper:
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
      "Work experience",
      ElementType.SPAN,
      self.__context_element
    )

  def resolve(self) -> None:
    self.__remove_all_work_experience()
    time.sleep(0.1)
    self.__add_all_work_experience()

  def __remove_all_work_experience(self) -> None:
    while True:
      if not self.__is_work_experience():
        break
      self.__remove_top_work_experience()
      time.sleep(0.1)

  def __is_work_experience(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Remove",
      ElementType.SPAN,
      self.__context_element
    )

  def __remove_top_work_experience(self) -> None:
    assert self.__is_work_experience()
    top_work_experience_remove_span = self.__selenium_helper.get_element_by_exact_text(
      "Remove",
      ElementType.SPAN,
      self.__context_element
    )
    top_work_experience_remove_button = top_work_experience_remove_span.find_element(By.XPATH, "..")
    top_work_experience_remove_button.click()
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

  def __add_all_work_experience(self) -> None:
    work_experience = self.__universal_config.about_me.work_experience
    for experience in work_experience:
      add_more_span = self.__selenium_helper.get_element_by_exact_text(
        "Add more",
        ElementType.SPAN,
        self.__context_element
      )
      add_more_button = add_more_span.find_element(By.XPATH, "..")
      add_more_button.click()
      self.__add_title(experience.title)
      self.__add_company(experience.company)
      if experience.currently_work_here:
        self.__click_currently_work_here()
      self.__add_start_time(experience.start)
      if not experience.currently_work_here:
        self.__add_end_time(experience.end)
      self.__save()

  def __add_title(self, job_title: str) -> None:
    title_label = self.__selenium_helper.get_element_by_exact_text(
      "Your title",
      ElementType.LABEL,
      self.__context_element
    )
    title_input = self.__get_input_from_label(title_label)
    self.__selenium_helper.write_to_input(job_title, title_input)

  def __add_company(self, company: str) -> None:
    company_label = self.__selenium_helper.get_element_by_exact_text(
      "Company",
      ElementType.LABEL,
      self.__context_element
    )
    company_input = self.__get_input_from_label(company_label)
    self.__selenium_helper.write_to_input(company, company_input)

  def __click_currently_work_here(self) -> None:
    currently_work_here_label = self.__selenium_helper.get_element_by_exact_text(
      "I currently work here",
      ElementType.LABEL,
      self.__context_element
    )
    currently_work_here_label.click()

  def __add_start_time(self, start: Date) -> None:
    relative_start_time_fieldset_xpath = "./div[2]/div/div[2]/form/div[1]/div/div[1]/div[3]/div[2]/div/div[1]/fieldset[1]"    # pylint: disable=line-too-long
    start_time_fieldset = self.__context_element.find_element(By.XPATH, relative_start_time_fieldset_xpath)
    relative_start_month_select_xpath = "./div/span[1]/select"
    start_month_select = Select(start_time_fieldset.find_element(By.XPATH, relative_start_month_select_xpath))
    start_month_select.select_by_index(start.month)
    relative_start_year_select_xpath = "./div/span[2]/select"
    start_year_select = Select(start_time_fieldset.find_element(By.XPATH, relative_start_year_select_xpath))
    start_year_select.select_by_value(str(start.year))

  def __add_end_time(self, end: Date) -> None:
    relative_end_time_fieldset_xpath = "./div[2]/div/div[2]/form/div[1]/div/div[1]/div[3]/div[2]/div/div[1]/fieldset[2]"
    end_time_fieldset = self.__context_element.find_element(By.XPATH, relative_end_time_fieldset_xpath)
    relative_end_month_select_xpath = "./div/span[1]/select"
    end_month_select = Select(end_time_fieldset.find_element(By.XPATH, relative_end_month_select_xpath))
    end_month_select.select_by_index(end.month)
    relative_end_year_select_xpath = "./div/span[2]/select"
    end_year_select = Select(end_time_fieldset.find_element(By.XPATH, relative_end_year_select_xpath))
    end_year_select.select_by_value(str(end.year))

  def __get_input_from_label(self, label: WebElement) -> WebElement:
    input_id = label.get_attribute("for")
    if input_id:
      input_el = self.__context_element.find_element(By.ID, input_id)
      return input_el
    raise NoSuchElementException("Invalid label_text.")

  def __save(self) -> None:
    save_span = self.__selenium_helper.get_element_by_exact_text(
      "Save",
      ElementType.SPAN,
      self.__context_element
    )
    save_button = save_span.find_element(By.XPATH, "..")
    save_button.click()
