import logging
import math
import sys
import time
from typing import List, Tuple
import psutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
  ElementClickInterceptedException,
  ElementNotInteractableException,
  NoSuchElementException,
  StaleElementReferenceException,
  TimeoutException
)
from entities.linkedin_job_listing import LinkedinJobListing
from entities.job_application import JobApplication
from exceptions.no_matching_jobs_page_exception import NoMatchingJobsPageException
from models.configs.quick_settings import QuickSettings
from models.enums.element_type import ElementType
from models.configs.linkedin_config import LinkedinConfig
from models.configs.universal_config import UniversalConfig
from models.enums.platform import Platform
from services.misc.database_manager import DatabaseManager
from services.misc.proxy_manager import ProxyManager
from services.pages.linkedin_apply_now_page.linkedin_apply_now_page import LinkedinApplyNowPage
from services.misc.selenium_helper import SeleniumHelper
from services.misc.language_parser import LanguageParser


class LinkedinJobListingsPage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __universal_config: UniversalConfig
  __quick_settings: QuickSettings
  __database_manager: DatabaseManager
  __language_parser: LanguageParser
  __linkedin_apply_now_page: LinkedinApplyNowPage
  __proxy_manager: ProxyManager
  __jobs_applied_to_this_session: List[dict[str, str | float | None]]

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    database_manager: DatabaseManager,
    language_parser: LanguageParser,
    universal_config: UniversalConfig,
    quick_settings: QuickSettings,
    linkedin_config: LinkedinConfig,
    proxy_manager: ProxyManager
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__database_manager = database_manager
    self.__language_parser = language_parser
    self.__universal_config = universal_config
    self.__quick_settings = quick_settings
    self.__linkedin_apply_now_page = LinkedinApplyNowPage(
      driver,
      selenium_helper,
      quick_settings,
      universal_config,
      linkedin_config
    )
    self.__proxy_manager = proxy_manager
    self.__jobs_applied_to_this_session = []

  def handle_current_query(self) -> None:
    total_jobs_tried = 0
    job_listing_li_index = 0
    while True:
      total_jobs_tried, job_listing_li_index = self.__handle_incrementors(total_jobs_tried, job_listing_li_index)
      try:
        self.__handle_page_context(total_jobs_tried)
      except NoSuchElementException:
        logging.info("No Job Listings left -- Finished with query.")
        return
      except NoMatchingJobsPageException:
        logging.info("No Job Listings left -- Finished with query.")
        return
      if self.__is_no_matching_jobs_page():
        logging.info("No matching jobs... Ending query.")
        return
      job_listing_li = self.__get_job_listing_li(job_listing_li_index)
      if job_listing_li is None:
        logging.info("No Job Listings left -- Finished with query.")
        return
      brief_job_listing = self.__build_brief_job_listing(job_listing_li_index)
      self.__add_job_listing_to_db(brief_job_listing)
      brief_job_listing.print()
      if brief_job_listing.to_minimal_dict() in self.__jobs_applied_to_this_session:
        logging.info("Ignoring Brief Job Listing because we've already applied this session. Skipping...")
        continue
      brief_job_application = JobApplication(self.__quick_settings, self.__universal_config, brief_job_listing)
      if not brief_job_application.applied():
        logging.info("Ignoring Brief Job Listing because it doesn't pass the filter check. Skipping...")
        self.__add_application_to_db(brief_job_application)
        continue
      if self.__something_went_wrong():
        logging.info('"Something went wrong", likely rate limited behavior. Skipping...')
        continue
      try:
        self.__select_job(job_listing_li)
      except StaleElementReferenceException:
        job_listing_li = self.__get_job_listing_li(job_listing_li_index)
      job_listing = self.__build_job_listing(job_listing_li_index)
      self.__add_job_listing_to_db(job_listing)
      job_application = JobApplication(self.__quick_settings, self.__universal_config, job_listing)
      if not job_application.applied():
        logging.info("Ignoring Job Listing because it doesn't pass the filter check. Skipping...")
        self.__add_application_to_db(job_application)
        continue
      if not self.__is_apply_button() and not self.__is_easy_apply_button():
        logging.info("This Job Listing has no apply button. Skipping...")
        continue
      try:
        self.__apply_to_selected_job()
      except NoMatchingJobsPageException:
        input("Lets get a proper logging statement in here -- what happened?")
      self.__driver.switch_to.window(self.__driver.window_handles[0])
      self.__jobs_applied_to_this_session.append(job_listing.to_minimal_dict())
      self.__add_application_to_db(job_application)
      self.__handle_potential_overload()

  def __handle_incrementors(self, total_jobs_tried: int, job_listing_li_index: int) -> Tuple[int, int]:
    total_jobs_tried += 1
    if total_jobs_tried >= 4:
      self.__selenium_helper.scroll_down(self.__get_job_listings_ul())
    job_listing_li_index = total_jobs_tried % 26
    if job_listing_li_index == 0:
      total_jobs_tried += 1
      job_listing_li_index = 1
    return (total_jobs_tried, job_listing_li_index)

  def __select_job(self, job_listing_li: WebElement, timeout=60) -> None:
    assert not self.__job_listing_li_is_active(job_listing_li)
    self.__selenium_helper.scroll_into_view(job_listing_li)
    self.__click_job_listing_li(job_listing_li)
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self.__job_listing_li_is_active(job_listing_li):
        return
      logging.debug("Waiting for Job Listing li to be active to confirm Job Listing click...")
      time.sleep(0.1)
    raise TimeoutError("Timed out waiting for full Job Listing to load.")

  def __job_listing_li_is_active(self, job_listing_li: WebElement) -> bool:
    active_class = "job-card-job-posting-card-wrapper--active"
    try:
      job_listing_li.find_element(By.CLASS_NAME, active_class)
      return True
    except NoSuchElementException:
      return False

  def __click_job_listing_li(self, job_listing_li: WebElement) -> None:
    while True:
      try:
        job_listing_li.click()
        time.sleep(0.1)
        return
      except ElementClickInterceptedException:
        self.__handle_potential_problems()
        logging.debug("Attempting to click Job Listing li...")
        time.sleep(0.1)

  def __handle_page_context(self, total_jobs_tried: int) -> None:
    if total_jobs_tried > 26 and total_jobs_tried % 26 == 1:
      logging.info("Attempting to go to page: %s...", math.ceil(total_jobs_tried / 26))
      next_page_span = self.__get_next_page_span()
      while True:
        try:
          next_page_span.click()
          while True:
            if self.__is_job_listings_ul():
              break
            if self.__is_no_matching_jobs_page():
              raise NoMatchingJobsPageException()
            logging.info("Waiting for next page to load...")
            time.sleep(0.1)
          return
        except ElementNotInteractableException:
          logging.debug("Failed to click next page span... Scrolling down and trying again...")
          self.__selenium_helper.scroll_down(self.__get_job_listings_ul())
          time.sleep(0.1)

  def __apply_to_selected_job(self) -> None:
    logging.info("Applying to job...")
    self.__wait_for_any_apply_button()
    if self.__is_easy_apply_button():
      self.__apply_on_linkedin()
    elif self.__is_apply_button():
      assert not self.__quick_settings.bot_behavior.easy_apply_only.linkedin
      self.__apply_on_company_site()
    else:
      raise RuntimeError("An apply button is found, but doesn't meet criteria of either apply button.")

  def __wait_for_new_tab_to_open(self, starting_tab_count: int, timeout=10) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      if len(self.__driver.window_handles) > starting_tab_count:
        time.sleep(0.1)   # This little bit of buffer time seems to help with some issues
        return
      self.__handle_potential_problems()
      logging.debug("Waiting for new tab to open...")
      time.sleep(0.1)
    raise TimeoutError("Timed out waiting for a new tab to open...")

  def __click_apply_button(self) -> None:
    self.__wait_for_apply_button()
    apply_button = self.__get_apply_button()
    apply_span = apply_button.find_element(By.XPATH, "./span")
    apply_span.click()

  def __click_easy_apply_button(self) -> None:
    self.__wait_for_easy_apply_button()
    easy_apply_button = self.__get_easy_apply_button()
    easy_apply_span = easy_apply_button.find_element(By.XPATH, "./span")
    easy_apply_span.click()

  def __apply_on_linkedin(self) -> None:
    logging.debug("Applying in new tab...")
    url = self.__driver.current_url
    self.__selenium_helper.open_new_tab()
    self.__driver.get(url)
    self.__click_easy_apply_button()
    self.__linkedin_apply_now_page.apply()
    self.__driver.switch_to.window(self.__driver.window_handles[0])

  def __apply_on_company_site(self) -> None:
    starting_tab_count = len(self.__driver.window_handles)
    self.__click_apply_button()
    try:
      self.__wait_for_new_tab_to_open(starting_tab_count)
    except TimeoutError:
      # Weird bug where occasionally the Linkedin apply button does nothing
      logging.warning("Apply button is dead... skipping...")

  def __build_brief_job_listing(self, index: int, timeout=4.0) -> LinkedinJobListing:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_listing_li = self.__get_job_listing_li(index)
        if job_listing_li is None:
          continue
        self.__selenium_helper.scroll_into_view(job_listing_li)
        job_listing = LinkedinJobListing(
          self.__language_parser,
          job_listing_li
        )
        return job_listing
      except StaleElementReferenceException:
        logging.warning("StaleElementReferenceException while trying to build brief job listing. Trying again...")
        time.sleep(0.1)
      except NoSuchElementException:
        logging.warning("NoSuchElementException while trying to build brief job listing. Trying again...")
        time.sleep(0.1)
    raise NoSuchElementException("Failed to find full job details div.")

  def __build_job_listing(self, index: int, timeout=4.0) -> LinkedinJobListing:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_description_content_div = self.__get_job_description_content_div()
        job_listing_li = self.__get_job_listing_li(index)
        if job_listing_li is None:
          continue
        self.__selenium_helper.scroll_into_view(job_listing_li)
        job_listing = LinkedinJobListing(
          self.__language_parser,
          job_listing_li,
          job_description_content_div,
          self.__driver.current_url
        )
        return job_listing
      except StaleElementReferenceException:
        logging.warning("StaleElementReferenceException while trying to build job listing. Trying again...")
        time.sleep(0.1)
      except NoSuchElementException:
        logging.warning("NoSuchElementException while trying to build job listing. Trying again...")
        time.sleep(0.1)
    raise NoSuchElementException("Failed to find full job details div.")

  def __get_job_description_content_div(self, timeout=5.0) -> WebElement:
    job_description_content_div_selector = "div.jobs-description-content__text--stretch"
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_description_content_div = self.__driver.find_element(By.CSS_SELECTOR, job_description_content_div_selector)
        return job_description_content_div
      except NoSuchElementException:
        logging.info("Waiting for job description content div...")
        time.sleep(0.1)
    raise TimeoutException("Timed out waiting for job description content div.")

  def __get_full_job_details_div(self) -> WebElement | None:
    full_job_details_div_selector = ".jobs-details__main-content.jobs-details__main-content--single-pane.full-width"
    main_content_div = self.__get_main_content_div()
    if main_content_div is None:
      return None
    while True:
      try:
        full_job_details_div = main_content_div.find_element(By.CSS_SELECTOR, full_job_details_div_selector)
        break
      except NoSuchElementException:
        self.__handle_potential_problems()
        logging.debug("Waiting for full job details div to load...")
        time.sleep(0.1)
      except StaleElementReferenceException:
        main_content_div = self.__get_main_content_div()
        if main_content_div is None:
          return None
    return full_job_details_div

  def __get_job_listing_li(self, index: int) -> WebElement | None:
    relative_job_listing_li_xpath = f"./li[{index}]"
    job_listings_ul = self.__get_job_listings_ul()
    if job_listings_ul is None:
      return None
    try:
      job_listing_li = job_listings_ul.find_element(By.XPATH, relative_job_listing_li_xpath)
    except NoSuchElementException:
      return None
    return job_listing_li

  def __is_job_listings_ul(self) -> bool:
    try:
      linkedin_footer = self.__selenium_helper.get_element_by_aria_label(
        "LinkedIn Footer Content",
        self.__get_main_content_div()
      )
      linkedin_footer.find_element(By.XPATH, "..")
      return True
    except NoSuchElementException:
      return False
    except StaleElementReferenceException:
      return False

  def __get_job_listings_ul(self, timeout=10) -> WebElement | None:
    logging.debug("Getting Job Listings ul...")
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        linkedin_footer = self.__selenium_helper.get_element_by_aria_label(
          "LinkedIn Footer Content",
          self.__get_main_content_div()
        )
        job_listings_ul = linkedin_footer.find_element(By.XPATH, "..")
        return job_listings_ul
      except NoSuchElementException:
        logging.debug("Waiting for Job Listings ul...")
        time.sleep(0.1)
      except StaleElementReferenceException:
        logging.debug("Waiting for Job Listings ul...")
        time.sleep(0.1)
    raise NoSuchElementException("Failed to find Job Listings ul.")

  def __get_main_content_div(self) -> WebElement | None:
    main_content_div_id = "main"
    return self.__driver.find_element(By.ID, main_content_div_id)

  def __get_next_page_span(self) -> WebElement:
    logging.debug("Getting next page button...")
    main_content_div = self.__get_main_content_div()
    return self.__selenium_helper.get_element_by_aria_label(
      "View next page",
      base_element=main_content_div
    )

  def __wait_for_any_apply_button(self) -> None:
    while True:
      if self.__is_apply_button():
        return
      elif self.__is_easy_apply_button():
        return
      logging.debug("Waiting for any apply button...")
      time.sleep(0.1)

  def __wait_for_apply_button(self) -> None:
    while not self.__is_apply_button():
      self.__handle_potential_problems()
      logging.debug("Waiting for apply button...")
      time.sleep(0.1)

  def __wait_for_easy_apply_button(self) -> None:
    while not self.__is_easy_apply_button():
      self.__handle_potential_problems()
      logging.debug("Waiting for Easy Apply button...")
      time.sleep(0.1)

  def __is_apply_button(self) -> bool:
    apply_button_id = "jobs-apply-button-id"
    try:
      full_job_details_div = self.__get_full_job_details_div()
      if full_job_details_div is None:
        return False
      apply_button = full_job_details_div.find_element(By.ID, apply_button_id)
      apply_span = apply_button.find_element(By.XPATH, "./span")
      if apply_span.text.lower().strip() == "apply":
        return True
      return False
    except NoSuchElementException:
      return False

  def __is_easy_apply_button(self) -> bool:
    easy_apply_button_id = "jobs-apply-button-id"
    try:
      full_job_details_div = self.__get_full_job_details_div()
      if full_job_details_div is None:
        return False
      easy_apply_button = full_job_details_div.find_element(By.ID, easy_apply_button_id)
      easy_apply_span = easy_apply_button.find_element(By.XPATH, "./span")
      if easy_apply_span.text.lower().strip() == "easy apply":
        return True
      return False
    except NoSuchElementException:
      return False

  def __get_apply_button(self) -> WebElement:
    apply_span = self.__selenium_helper.get_element_by_exact_text(
      "Apply",
      ElementType.SPAN,
      self.__get_full_job_details_div()
    )
    apply_button = apply_span.find_element(By.XPATH, "..")
    return apply_button

  def __get_easy_apply_button(self) -> WebElement:
    easy_apply_span = self.__selenium_helper.get_element_by_exact_text(
      "Easy Apply",
      ElementType.SPAN,
      self.__get_full_job_details_div()
    )
    easy_apply_button = easy_apply_span.find_element(By.XPATH, "..")
    return easy_apply_button

  def __is_no_matching_jobs_page(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "No matching jobs found",
      ElementType.H2
    )

  def __handle_potential_problems(self) -> None:
    if self.__is_job_safety_reminder_popup():
      self.__remove_job_search_safety_reminder_popup()
    elif self.__something_went_wrong():
      self.__driver.refresh()
      time.sleep(5)   # It seems that if you don't wait here, the issue will arise again -- likely rate limiting
    elif self.__is_rate_limited_page():
      self.__handle_rate_limited_page()
    elif self.__is_no_matching_jobs_page():
      raise NoMatchingJobsPageException()

  def __something_went_wrong(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Something went wrong",
      ElementType.H2
    )

  def __is_job_safety_reminder_popup(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Job search safety reminder",
      ElementType.H2
    )

  def __remove_job_search_safety_reminder_popup(self) -> None:
    assert self.__is_job_safety_reminder_popup()
    continue_applying_button_id = "jobs-apply-button-id"
    continue_applying_button = self.__driver.find_element(By.ID, continue_applying_button_id)
    continue_applying_button.click()

  def __is_rate_limited_page(self) -> bool:
    error_code_div_class = "error-code"
    try:
      self.__driver.find_element(By.CLASS_NAME, error_code_div_class)   # Confirm we're on HTTP error page
      return True
    except NoSuchElementException:
      return False

  def __handle_rate_limited_page(self) -> None:
    # TODO: Still brainstorming how to properly handle this
    self.__proxy_manager.log_rate_limit_block(Platform.LINKEDIN)
    input("Rate limited. :( Finish what's available and start again.")
    sys.exit(0)

  def __handle_potential_overload(self) -> None:
    jobs_open = len(self.__driver.window_handles) - 1
    pause_every_x_jobs = self.__quick_settings.bot_behavior.pause_every_x_jobs
    current_memory_usage = psutil.virtual_memory().percent
    logging.debug("Current memory usage: %s%s", current_memory_usage, "%")
    if (
      pause_every_x_jobs
      and jobs_open % pause_every_x_jobs == 0
      and jobs_open >= pause_every_x_jobs
    ):
      print(f"\nResponding to request to pause after every {pause_every_x_jobs} jobs.")
      input("\tPress enter to proceed...")
    elif current_memory_usage > 90:
      print("\nCurrent memory usage is too high. Please clean up existing tabs to continue safely.")
      input("\tPress enter to proceed...")

  def __add_job_listing_to_db(self, job_listing: LinkedinJobListing) -> None:
    self.__database_manager.create_new_job_listing(
      job_listing,
      Platform.LINKEDIN
    )

  def __add_application_to_db(self, job_application: JobApplication) -> None:
    self.__database_manager.create_new_application(
      job_application,
      Platform.LINKEDIN
    )
