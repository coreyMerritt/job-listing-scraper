import logging
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
  ElementClickInterceptedException,
  NoSuchElementException,
  StaleElementReferenceException
)
from models.configs.quick_settings import QuickSettings
from models.enums.element_type import ElementType
from models.configs.linkedin_config import LinkedinConfig
from models.configs.universal_config import UniversalConfig
from services.misc.selenium_helper import SeleniumHelper
from services.pages.linkedin_apply_now_page.steppers.linkedin_contact_info_stepper import LinkedinContactInfoStepper
from services.pages.linkedin_apply_now_page.steppers.linkedin_education_stepper import LinkedinEducationStepper
from services.pages.linkedin_apply_now_page.steppers.linkedin_home_address_stepper import LinkedinHomeAddressStepper
from services.pages.linkedin_apply_now_page.steppers.linkedin_privacy_policy_stepper import LinkedinPrivacyPolicyStepper
from services.pages.linkedin_apply_now_page.steppers.linkedin_resume_stepper import LinkedinResumeStepper
from services.pages.linkedin_apply_now_page.steppers.linkedin_voluntary_self_identification_stepper import LinkedinVoluntarySelfIdentificationStepper        # pylint: disable=line-too-long
from services.pages.linkedin_apply_now_page.steppers.linkedin_work_experience_stepper import LinkedinWorkExperienceStepper     # pylint: disable=line-too-long


class LinkedinApplyNowPage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __quick_settings: QuickSettings
  __easy_apply_div: WebElement
  __contact_info_stepper: LinkedinContactInfoStepper
  __home_address_stepper: LinkedinHomeAddressStepper
  __resume_stepper: LinkedinResumeStepper
  __voluntary_self_indentification_stepper: LinkedinVoluntarySelfIdentificationStepper
  __work_experience_stepper: LinkedinWorkExperienceStepper
  __education_stepper: LinkedinEducationStepper
  __privacy_policy_stepper: LinkedinPrivacyPolicyStepper

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    quick_settings: QuickSettings,
    universal_config: UniversalConfig,
    linkedin_config: LinkedinConfig
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__quick_settings = quick_settings
    self.__contact_info_stepper = LinkedinContactInfoStepper(
      driver,
      selenium_helper,
      universal_config,
      linkedin_config
    )
    self.__home_address_stepper = LinkedinHomeAddressStepper(
      selenium_helper,
      universal_config
    )
    self.__resume_stepper = LinkedinResumeStepper(
      driver,
      selenium_helper,
      universal_config
    )
    self.__voluntary_self_indentification_stepper = LinkedinVoluntarySelfIdentificationStepper(
      selenium_helper,
      universal_config
    )
    self.__work_experience_stepper = LinkedinWorkExperienceStepper(
      driver,
      selenium_helper,
      universal_config
    )
    self.__education_stepper = LinkedinEducationStepper(
      driver,
      selenium_helper,
      universal_config
    )
    self.__privacy_policy_stepper = LinkedinPrivacyPolicyStepper(
      selenium_helper
    )

  def is_present(self) -> bool:
    try:
      easy_apply_div_xpath = "/html/body/div[4]/div/div"
      self.__driver.find_element(By.XPATH, easy_apply_div_xpath)
      return True
    except NoSuchElementException:
      return False

  def apply(self) -> None:
    logging.debug("Filling out application...")
    self.__reset_contexts()
    try:
      while self.is_present():
        self.__wait_for_some_stepper()
        if self.__contact_info_stepper.is_present():
          self.__contact_info_stepper.resolve()
        elif self.__home_address_stepper.is_present():
          self.__home_address_stepper.resolve()
        elif self.__resume_stepper.is_present():
          self.__resume_stepper.resolve()
        elif self.__voluntary_self_indentification_stepper.is_present():
          self.__voluntary_self_indentification_stepper.resolve()
        elif self.__work_experience_stepper.is_present():
          self.__work_experience_stepper.resolve()
        elif self.__education_stepper.is_present():
          self.__education_stepper.resolve()
        elif self.__privacy_policy_stepper.is_present():
          self.__privacy_policy_stepper.resolve()
        if self.__is_automation_roadblock():
          return
        elif self.__is_final_stepper():
          if self.__is_easy_apply_scrollable_div():
            self.__selenium_helper.scroll_to_bottom(self.__get_easy_apply_scrollable_div())
          return
        else:
          self.__continue_stepper()
          time.sleep(0.5)
          if self.__some_field_was_left_blank():
            if self.__quick_settings.bot_behavior.pause_on_unknown_stepper:
              input("Unknown stepper found. Press enter to continue...")
    except StaleElementReferenceException:
      logging.debug("StaleElementReferenceException. Querying for new easy_apply_div...")
      self.__reset_contexts()

  def __wait_for_some_stepper(self) -> None:
    while True:
      if self.__selenium_helper.exact_text_is_present(
        "Submitting this application won’t change your LinkedIn profile.",
        ElementType.PARAGRAPH,
        self.__easy_apply_div
      ):
        time.sleep(0.1)
        return
      if self.__is_final_stepper():
        time.sleep(0.1)
        return
      if self.__is_job_search_safety_reminder():
        logging.debug("Found job search safety reminder. Removing...")
        self.__remove_job_search_safety_reminder()
      logging.debug("Waiting for stepper to load...")
      time.sleep(0.1)

  def __reset_contexts(self) -> None:
    easy_apply_div_xpath = "/html/body/div[4]/div/div"
    easy_apply_div = self.__driver.find_element(By.XPATH, easy_apply_div_xpath)
    self.__easy_apply_div = easy_apply_div
    self.__contact_info_stepper.set_context(easy_apply_div)
    self.__education_stepper.set_context(easy_apply_div)
    self.__home_address_stepper.set_context(easy_apply_div)
    self.__privacy_policy_stepper.set_context(easy_apply_div)
    self.__resume_stepper.set_context(easy_apply_div)
    self.__voluntary_self_indentification_stepper.set_context(easy_apply_div)
    self.__work_experience_stepper.set_context(easy_apply_div)

  def __is_automation_roadblock(self) -> bool:
    return (
      self.__selenium_helper.exact_text_is_present("Additional", ElementType.H3, self.__easy_apply_div)
      or self.__selenium_helper.exact_text_is_present("Additional Questions", ElementType.H3, self.__easy_apply_div)
    )

  def __is_final_stepper(self) -> bool:
    return (
      self.__selenium_helper.exact_text_is_present("Submit application", ElementType.BUTTON, self.__easy_apply_div)
      or self.__selenium_helper.exact_text_is_present('Review your application', ElementType.H3, self.__easy_apply_div)
    )

  def __continue_stepper(self) -> None:
    element_to_search = self.__easy_apply_div
    while True:
      try:
        next_span = self.__selenium_helper.get_element_by_exact_text("Next", ElementType.SPAN, element_to_search)
        next_button = next_span.find_element(By.XPATH, "..")
        next_button.click()
        return
      except ElementClickInterceptedException:
        logging.debug("ElementClickInterceptedException. Trying again...")
        time.sleep(0.1)
      except NoSuchElementException:
        if self.__is_job_search_safety_reminder():
          logging.debug("Found job search safety reminder. Removing...")
          self.__remove_job_search_safety_reminder()
        else:
          logging.debug("NoSuchElementException. Trying again...")
          time.sleep(0.1)
      try:
        review_span = self.__selenium_helper.get_element_by_exact_text("Review", ElementType.SPAN, element_to_search)
        review_button = review_span.find_element(By.XPATH, "..")
        review_button.click()
        return
      except ElementClickInterceptedException:
        logging.debug("ElementClickInterceptedException. Trying again...")
        time.sleep(0.1)
      except NoSuchElementException:
        if self.__is_job_search_safety_reminder():
          logging.debug("Found job search safety reminder. Removing...")
          self.__remove_job_search_safety_reminder()
        else:
          logging.debug("NoSuchElementException. Trying again...")
          time.sleep(0.1)

  def __some_field_was_left_blank(self) -> bool:
    error_message_class = "artdeco-inline-feedback__message"
    try:
      error_message = self.__easy_apply_div.find_element(By.CLASS_NAME, error_message_class)
      if error_message.is_displayed():
        return True
      return False
    except NoSuchElementException:
      return False

  def __is_easy_apply_scrollable_div(self) -> bool:
    easy_apply_scrollable_div_xpath = "/html/body/div[4]/div/div/div[2]"
    try:
      self.__driver.find_element(By.XPATH, easy_apply_scrollable_div_xpath)
      return True
    except NoSuchElementException:
      return False

  def __get_easy_apply_scrollable_div(self) -> WebElement:
    assert self.__is_easy_apply_scrollable_div()
    easy_apply_scrollable_div_xpath = "/html/body/div[4]/div/div/div[2]"
    easy_apply_scrollable_div = self.__driver.find_element(By.XPATH, easy_apply_scrollable_div_xpath)
    return easy_apply_scrollable_div

  def __is_job_search_safety_reminder(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Continue applying",
      ElementType.SPAN
    )

  def __remove_job_search_safety_reminder(self) -> None:
    continue_applying_span = self.__selenium_helper.get_element_by_exact_text(
      "Continue applying",
      ElementType.SPAN
    )
    continue_applying_button = continue_applying_span.find_element(By.XPATH, "..")
    continue_applying_button.click()
