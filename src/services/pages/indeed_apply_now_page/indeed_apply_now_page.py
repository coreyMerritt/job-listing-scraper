import logging
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from models.enums.element_type import ElementType
from services.misc.selenium_helper import SeleniumHelper
from services.pages.indeed_apply_now_page.steppers.indeed_commute_check_stepper import IndeedCommuteCheckStepper
from services.pages.indeed_apply_now_page.steppers.indeed_contact_info_stepper import IndeedContactInfoStepper
from services.pages.indeed_apply_now_page.steppers.indeed_location_stepper import IndeedLocationStepper
from services.pages.indeed_apply_now_page.steppers.indeed_relevant_experience_stepper import (
  IndeedRelevantExperienceStepper
)
from services.pages.indeed_apply_now_page.steppers.indeed_resume_stepper import IndeedResumeStepper


class IndeedApplyNowPage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __quick_settings: QuickSettings
  __relevant_experience_stepper: IndeedRelevantExperienceStepper
  __resume_stepper: IndeedResumeStepper
  __location_stepper: IndeedLocationStepper
  __contact_info_stepper: IndeedContactInfoStepper
  __commute_check_stepper: IndeedCommuteCheckStepper

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    universal_config: UniversalConfig,
    quick_settings: QuickSettings
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__quick_settings = quick_settings
    self.__relevant_experience_stepper = IndeedRelevantExperienceStepper(
      driver,
      selenium_helper,
      universal_config
    )
    self.__resume_stepper = IndeedResumeStepper(
      driver,
      selenium_helper,
      universal_config
    )
    self.__location_stepper = IndeedLocationStepper(
      driver,
      selenium_helper,
      universal_config
    )
    self.__contact_info_stepper = IndeedContactInfoStepper(
      driver,
      selenium_helper,
      universal_config
    )
    self.__commute_check_stepper = IndeedCommuteCheckStepper(
      driver
    )

  def is_present(self) -> bool:
    return "smartapply.indeed.com" in self.__driver.current_url

  def apply(self) -> None:
    POTENTIAL_ALREADY_APPLIED_URL = "smartapply.indeed.com/beta/indeedapply/postresumeapply"
    ALREADY_APPLIED_URL = "smartapply.indeed.com/beta/indeedapply/form/applied"
    REVIEW_URL = "smartapply.indeed.com/beta/indeedapply/form/review"
    while self.is_present():
      self.__wait_for_some_stepper()
      if self.__relevant_experience_stepper.is_present():
        self.__relevant_experience_stepper.resolve()
      elif self.__resume_stepper.is_present():
        self.__resume_stepper.resolve()
      elif self.__location_stepper.is_present():
        self.__location_stepper.resolve()
      elif self.__contact_info_stepper.is_present():
        self.__contact_info_stepper.resolve()
      elif self.__commute_check_stepper.is_present():
        self.__commute_check_stepper.resolve()
      if self.__is_automation_roadblock():
        self.__driver.switch_to.window(self.__driver.window_handles[0])
        return
      elif ALREADY_APPLIED_URL in self.__driver.current_url:
        self.__driver.close()
        self.__driver.switch_to.window(self.__driver.window_handles[0])
        return
      elif POTENTIAL_ALREADY_APPLIED_URL in self.__driver.current_url:
        IS_GENUINE_ALREADY_APPLIED_PAGE = self.__is_already_applied_page(POTENTIAL_ALREADY_APPLIED_URL)
        if IS_GENUINE_ALREADY_APPLIED_PAGE:
          self.__driver.close()
          self.__driver.switch_to.window(self.__driver.window_handles[0])
          return
      elif REVIEW_URL in self.__driver.current_url:
        self.__selenium_helper.scroll_to_bottom()
        self.__driver.switch_to.window(self.__driver.window_handles[0])
        return
      else:
        time.sleep(0.5)
        self.__click_continue_button()
        time.sleep(0.5)
        if False: # TODO: Figure out how to clearly determine when a stepper is not filled -- see LinkedinApplyNowPage
          if self.__quick_settings.bot_behavior.pause_on_unknown_stepper:
            input("Unknown stepper found. Press enter to continue...")

  def __wait_for_some_stepper(self) -> None:
    while not self.__selenium_helper.exact_aria_label_is_present("Progress"):
      logging.debug("Waiting for some stepper to load...")
      time.sleep(0.1)
    time.sleep(0.5)

  def __is_already_applied_page(self, potential_already_applied_url: str) -> bool:
    confirm_time = 7
    start_time = time.time()
    IS_GENUINE_ALREADY_APPLIED_PAGE = True
    while time.time() - start_time < confirm_time:
      if not potential_already_applied_url in self.__driver.current_url:
        IS_GENUINE_ALREADY_APPLIED_PAGE = False
        break
    return IS_GENUINE_ALREADY_APPLIED_PAGE

  def __is_automation_roadblock(self) -> bool:
    VAGUE_QUESTIONS_URL = "smartapply.indeed.com/beta/indeedapply/form/questions-module/questions/1"
    DEMOGRAPHIC_QUESTIONS_URL = "smartapply.indeed.com/beta/indeedapply/form/demographic-questions/1"
    ADDITIONAL_DOCUMENTS_URL = "smartapply.indeed.com/beta/indeedapply/form/resume-module/additional-documents"
    return (
      VAGUE_QUESTIONS_URL in self.__driver.current_url
      or DEMOGRAPHIC_QUESTIONS_URL in self.__driver.current_url
      or ADDITIONAL_DOCUMENTS_URL in self.__driver.current_url
    )

  def __click_continue_button(self) -> None:
    try:
      self.__driver.find_element(By.TAG_NAME, "body").click()
      time.sleep(0.1)
      continue_span = self.__selenium_helper.get_element_by_exact_text(
        "Continue",
        ElementType.SPAN
      )
      continue_button = continue_span.find_element(By.XPATH, "..")
      continue_button.click()
    except NoSuchElementException:
      logging.debug("Failed to click continue button. Trying again...")
      time.sleep(0.1)
