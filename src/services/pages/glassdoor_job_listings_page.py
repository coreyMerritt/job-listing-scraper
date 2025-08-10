import logging
import time
from typing import List
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
from entities.glassdoor_job_listing import GlassdoorJobListing
from entities.glassdoor_show_more_jobs_button import GlassdoorShowMoreJobsButton
from exceptions.glassdoor_show_more_jobs_button_broken_exception import GlassdoorShowMoreJobsButtonBrokenException
from exceptions.no_more_job_listings_exception import NoMoreJobListingsException
from exceptions.page_didnt_load_exception import PageDidntLoadException
from exceptions.service_is_down_exception import ServiceIsDownException
from exceptions.zero_search_results_exception import ZeroSearchResultsException
from models.enums.element_type import ElementType
from models.enums.platform import Platform
from services.misc.database_manager import DatabaseManager
from services.misc.selenium_helper import SeleniumHelper
from services.misc.language_parser import LanguageParser


class GlassdoorJobListingsPage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __database_manager: DatabaseManager
  __language_parser: LanguageParser
  __current_session_jobs: List[dict[str, str | float | None]]
  __show_more_jobs_button: GlassdoorShowMoreJobsButton | None

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    database_manager: DatabaseManager,
    language_parser: LanguageParser
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__database_manager = database_manager
    self.__language_parser = language_parser
    self.__current_session_jobs = []
    self.__show_more_jobs_button = None

  def scrape_current_query(self) -> None:
    try:
      self.__confirm_page_stability()
    except ZeroSearchResultsException:
      logging.debug("Returned 0 results, skipping query.")
      return
    while self.__page_didnt_load_is_present():
      logging.debug("Waiting for page to load...")
      time.sleep(0.5)
    i = 0
    while self.__is_show_more_jobs_span():
      try:
        self.__safe_click_show_more_jobs_button()
      except PageDidntLoadException:
        logging.error("Page didnt load. Skipping query and moving to next...")
        input("DEBUG: ^^^")
        return
    while True:
      i += 1
      logging.debug("Looping through Job Listings: %s...", i)
      self.__remove_create_job_dialog()
      self.__remove_survey_popup()
      try:
        job_listing_li = self.__get_job_listing_li(i)
      except NoMoreJobListingsException:
        logging.info("No Job Listings remaining. Returning...")
        return
      self.__selenium_helper.scroll_into_view(job_listing_li)
      if not self.__is_job_listing(job_listing_li):
        continue
      brief_job_listing = GlassdoorJobListing(self.__language_parser, job_listing_li)
      self.__add_job_listing_to_db(brief_job_listing)
      brief_job_listing.print()
      if brief_job_listing.to_minimal_dict() in self.__current_session_jobs:
        logging.info("Ignoring Job Listing because: we've already applied this session.\n")
        continue
      self.__remove_create_job_dialog()
      self.__remove_survey_popup()
      job_listing_li.click()
      try:
        job_listing = self.__build_job_listing(i)
      except TimeoutError:
        logging.warning("Job info div failed to load. Skipping...")
        continue
      self.__add_job_listing_to_db(job_listing)
      self.__current_session_jobs.append(job_listing.to_minimal_dict())
      self.__handle_potential_overload()

  def __confirm_page_stability(self, timeout=60.0) -> None:
    start_time = time.time()
    count = 0
    while time.time() - start_time < timeout:
      try:
        if self.__returned_zero_results():
          raise ZeroSearchResultsException("Returned 0 results.")
        return
      except PageDidntLoadException as e:
        count += 1
        if count > 3:
          raise ServiceIsDownException("Glassdoor appears to be down -- receiving constant page load problems.") from e
        logging.warning("Page didnt load. Refreshing and trying again...")
        self.__driver.refresh()

  def __build_job_listing(self, index: int, timeout=30.0) -> GlassdoorJobListing:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_listing_li = self.__get_job_listing_li(index)
        self.__selenium_helper.scroll_into_view(job_listing_li)
        job_info_div = self.__get_job_info_div()
        job_listing = GlassdoorJobListing(
          self.__language_parser,
          job_listing_li,
          job_info_div,
          self.__driver.current_url
        )
        return job_listing
      except StaleElementReferenceException:
        if not self.__job_info_div_is_present():
          if self.__page_didnt_load_is_present():
            self.__reload_job_description()
        logging.warning("StaleElementReferenceException while trying to build job listing. Trying again...")
        time.sleep(0.1)
      except NoSuchElementException:
        logging.warning("NoSuchElementException while trying to build job listing. Trying again...")
        time.sleep(0.1)
    raise TimeoutException("Timed out trying to build job listing.")

  def __job_info_div_is_present(self) -> bool:
    job_info_div_xpath = "/html/body/div[4]/div[4]/div[2]/div[2]/div/div[1]"
    try:
      self.__driver.find_element(By.XPATH, job_info_div_xpath)
      return True
    except NoSuchElementException:
      return False

  def __page_didnt_load_is_present(self) -> bool:
    return self.__selenium_helper.exact_text_is_present("Zzzzzzzz...", ElementType.H1)

  def __reload_job_description(self) -> None:
    try_again_span = self.__selenium_helper.get_element_by_exact_text("Try again", ElementType.SPAN)
    parent_span = try_again_span.find_element(By.XPATH, "..")
    try_again_button = parent_span.find_element(By.XPATH, "..")
    try_again_button.click()
    self.__wait_for_job_info_div()

  def __get_job_listings_ul(self) -> WebElement:
    try:
      job_listings_ul = self.__selenium_helper.get_element_by_aria_label("Jobs List")
    except ElementClickInterceptedException:
      self.__remove_create_job_dialog()
      self.__remove_survey_popup()
      job_listings_ul = self.__selenium_helper.get_element_by_aria_label("Jobs List")
    except NoSuchElementException as e:
      if self.__page_didnt_load_is_present():
        raise PageDidntLoadException() from e
      self.__remove_create_job_dialog()
      self.__remove_survey_popup()
      job_listings_ul = self.__selenium_helper.get_element_by_aria_label("Jobs List")
    return job_listings_ul

  def __get_job_listing_li(self, index: int) -> WebElement:
    job_listings_ul = self.__get_job_listings_ul()
    while True:
      try:
        job_listing_li = job_listings_ul.find_element(By.XPATH, f"./li[{index}]")
        return job_listing_li
      except NoSuchElementException as e:
        if self.__is_show_more_jobs_span():
          self.__safe_click_show_more_jobs_button()
          self.__wait_for_new_job_listing_li(index + 1)
        else:
          raise NoMoreJobListingsException() from e
      except StaleElementReferenceException:
        logging.debug("Failed to get Job Listing li. Trying again...")
        job_listings_ul = self.__get_job_listings_ul()

  def __is_show_more_jobs_span(self) -> bool:
    self.__selenium_helper.scroll_to_bottom()
    try:
      job_listings_ul = self.__get_job_listings_ul()
      job_listings_ul.find_element(By.XPATH, "../div/div/button")
      return True
    except NoSuchElementException:
      return False

  def __refresh_show_more_jobs_button(self) -> None:
    if self.__is_show_more_jobs_span():
      self.__selenium_helper.scroll_to_bottom()
      while True:
        try:
          job_listings_ul = self.__get_job_listings_ul()
          self.__show_more_jobs_button = GlassdoorShowMoreJobsButton(job_listings_ul)
          return
        except NoSuchElementException:
          logging.debug("Waiting for job listings ul...")
          time.sleep(0.1)
    self.__show_more_jobs_button = None

  def __safe_click_show_more_jobs_button(self, timeout=30.0) -> None:
    if self.__show_more_jobs_button is None:
      self.__refresh_show_more_jobs_button()
      assert self.__show_more_jobs_button
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        starting_li_count = len(self.__get_job_listings_ul().find_elements(By.TAG_NAME, "li"))
        self.__show_more_jobs_button.click()
        self.__wait_for_more_job_listings(starting_li_count)
        return
      except ElementNotInteractableException:
        logging.debug("ElementNotInteractableException. Checking for dialogs and trying again...")
        self.__remove_create_job_dialog()
        self.__remove_survey_popup()
        time.sleep(0.1)
      except ElementClickInterceptedException:
        logging.debug("ElementClickInterceptedException. Checking for dialogs and trying again...")
        self.__remove_create_job_dialog()
        self.__remove_survey_popup()
        time.sleep(0.1)
      except StaleElementReferenceException:
        self.__refresh_show_more_jobs_button()
        time.sleep(0.1)
    raise TimeoutError("Timed out trying to show more jobs.")

  def __wait_for_more_job_listings(self, starting_li_count: int) -> None:
    confirm_more_job_listings_timeout = 10.0
    start_time = time.time()
    while time.time() - start_time < confirm_more_job_listings_timeout:
      ending_li_count = len(self.__get_job_listings_ul().find_elements(By.TAG_NAME, "li"))
      if starting_li_count != ending_li_count:
        break
    if starting_li_count == ending_li_count:
      if self.__is_show_more_jobs_span():
        raise GlassdoorShowMoreJobsButtonBrokenException("Button did not produce more <li>s")

  def __wait_for_new_job_listing_li(self, index: int, timeout=10) -> None:
    start_time = time.time()
    job_listings_ul = self.__get_job_listings_ul()
    while time.time() - start_time < timeout:
      try:
        job_listings_ul.find_element(By.XPATH, f"./li[{index}]")
        return
      except NoSuchElementException:
        logging.debug("Waiting for job listing li...")
        time.sleep(0.1)
    raise NoSuchElementException("Failed waiting for job listing li.")

  def __wait_for_job_info_div(self, timeout=10) -> None:
    job_info_div_xpath = "/html/body/div[4]/div[4]/div[2]/div[2]/div/div[1]"
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        self.__driver.find_element(By.XPATH, job_info_div_xpath)
        break
      except NoSuchElementException:
        logging.debug("Waiting for job info div to load...")
        time.sleep(0.1)

  def __get_job_info_div(self) -> WebElement:
    self.__wait_for_job_info_div()
    job_info_div_xpath = "/html/body/div[4]/div[4]/div[2]/div[2]/div/div[1]"
    job_info_div = self.__driver.find_element(By.XPATH, job_info_div_xpath)
    return job_info_div

  def __remove_create_job_dialog(self) -> None:
    create_job_alert_dialog_xpath = "/html/body/div[8]/div/dialog"
    relative_cancel_dialog_button_xpath = "./div[2]/div[1]/div[1]/button[1]"
    try:
      create_job_alert_dialog = self.__driver.find_element(By.XPATH, create_job_alert_dialog_xpath)
      cancel_button = create_job_alert_dialog.find_element(By.XPATH, relative_cancel_dialog_button_xpath)
      logging.debug("Removing create job dialog...")
      cancel_button.click()
    except NoSuchElementException:
      pass

  def __remove_survey_popup(self) -> None:
    exit_button_id = "qual_close_open"
    try:
      exit_button = self.__driver.find_element(By.ID, exit_button_id)
      exit_button.click()
    except NoSuchElementException:
      pass

  def __is_job_listing(self, element: WebElement) -> bool:
    attr = element.get_attribute("data-test")
    result = attr is not None and "jobListing" in attr
    logging.debug("Checked if is Job Listing: %s", result)
    return result

  def __returned_zero_results(self) -> bool:
    search_h1_class = "SearchResultsHeader_jobCount__eHngv"
    try:
      search_h1 = self.__driver.find_element(By.CLASS_NAME, search_h1_class)
      search_h1_text = search_h1.text.lower().strip()
      if len(search_h1_text) == 0:
        raise PageDidntLoadException()
      if search_h1_text[0] == "0":
        return True
      return False
    except NoSuchElementException:
      return False

  def __handle_potential_overload(self) -> None:
    current_memory_usage = psutil.virtual_memory().percent
    logging.debug("Current memory usage: %s%s", current_memory_usage, "%")
    if current_memory_usage > 90:
      print("\nCurrent memory usage is too high. Please clean up existing tabs to continue safely.")
      input("\tPress enter to proceed...")

  def __add_job_listing_to_db(self, job_listing: GlassdoorJobListing) -> None:
    self.__database_manager.create_new_job_listing(
      job_listing,
      Platform.GLASSDOOR
    )
