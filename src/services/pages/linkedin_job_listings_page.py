import logging
import math
import sys
import time
from typing import Set, Tuple
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
from exceptions.no_matching_jobs_page_exception import NoMatchingJobsPageException
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from models.enums.element_type import ElementType
from models.enums.platform import Platform
from services.misc.database_manager import DatabaseManager
from services.misc.job_criteria_checker import JobCriteriaChecker
from services.misc.proxy_manager import ProxyManager
from services.misc.selenium_helper import SeleniumHelper
from services.misc.language_parser import LanguageParser


class LinkedinJobListingsPage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __database_manager: DatabaseManager
  __language_parser: LanguageParser
  __proxy_manager: ProxyManager
  __criteria_checker: JobCriteriaChecker
  __quick_settings: QuickSettings
  __universal_config: UniversalConfig
  __current_session_jobs: Set[str]

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    database_manager: DatabaseManager,
    language_parser: LanguageParser,
    proxy_manager: ProxyManager,
    quick_settings: QuickSettings,
    universal_config: UniversalConfig
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__database_manager = database_manager
    self.__language_parser = language_parser
    self.__proxy_manager = proxy_manager
    self.__criteria_checker = JobCriteriaChecker()
    self.__quick_settings = quick_settings
    self.__universal_config = universal_config
    self.__current_session_jobs = set()

  def scrape_current_query(self) -> None:
    total_jobs_tried = 0
    job_listing_li_index = 0
    while True:
      # Increment
      total_jobs_tried, job_listing_li_index = self.__handle_incrementors(total_jobs_tried, job_listing_li_index)
      # Log
      logging.info("Attempting Job Listing: %s...", total_jobs_tried)
      # Validate page/context
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
      # Get Li, finished if cant
      job_listing_li = self.__get_job_listing_li(job_listing_li_index)
      if job_listing_li is None:
        logging.info("No Job Listings left -- Finished with query.")
        return
      # TODO: Lets get some sort of attr validation in here to confirm we have a true job listing li
      # Scroll into view
      self.__selenium_helper.scroll_into_view(job_listing_li)
      # Make Brief
      brief_job_listing = self.__build_brief_job_listing(job_listing_li_index)
      # Print Brief
      brief_job_listing.print()
      # If already handled, next
      if brief_job_listing.to_minimal_str() in self.__current_session_jobs:
        logging.info("Ignoring Brief Job Listing because we've already applied this session. Skipping...")
        continue
      # Add job to already handled
      self.__current_session_jobs.add(brief_job_listing.to_minimal_str())
      # Ensure job listing meets criteria
      if not self.__criteria_checker.passes(self.__quick_settings, self.__universal_config, brief_job_listing):
        logging.info("Ignoring Job Listing because it does not meet ignore/ideal criteria.")
        continue
      # If not full scrape, add to db and next
      if not self.__quick_settings.bot_behavior.full_scrape:
        self.__add_job_listing_to_db(brief_job_listing)
        continue
      # Click Job Listing
      try:
        self.__select_job(job_listing_li)
      except StaleElementReferenceException:
        job_listing_li = self.__get_job_listing_li(job_listing_li_index)
      # Make Job Listing
      job_listing = self.__build_job_listing(job_listing_li_index)
      # Ensure job listing meets criteria
      if not self.__criteria_checker.passes(self.__quick_settings, self.__universal_config, job_listing):
        logging.info("Ignoring Job Listing because it does not meet ignore/ideal criteria.")
        continue
      # Add to db
      self.__add_job_listing_to_db(job_listing)
      # Overload
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

  # TODO: Do we still need this?
  # def __get_full_job_details_div(self) -> WebElement | None:
  #   full_job_details_div_selector = ".jobs-details__main-content.jobs-details__main-content--single-pane.full-width"
  #   main_content_div = self.__get_main_content_div()
  #   if main_content_div is None:
  #     return None
  #   while True:
  #     try:
  #       full_job_details_div = main_content_div.find_element(By.CSS_SELECTOR, full_job_details_div_selector)
  #       break
  #     except NoSuchElementException:
  #       self.__handle_potential_problems()
  #       logging.debug("Waiting for full job details div to load...")
  #       time.sleep(0.1)
  #     except StaleElementReferenceException:
  #       main_content_div = self.__get_main_content_div()
  #       if main_content_div is None:
  #         return None
  #   return full_job_details_div

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
    current_memory_usage = psutil.virtual_memory().percent
    logging.debug("Current memory usage: %s%s", current_memory_usage, "%")
    if current_memory_usage > 90:
      print("\nCurrent memory usage is too high. Please clean up existing tabs to continue safely.")
      input("\tPress enter to proceed...")

  def __add_job_listing_to_db(self, job_listing: LinkedinJobListing) -> None:
    self.__database_manager.create_new_job_listing(
      job_listing,
      Platform.LINKEDIN
    )
