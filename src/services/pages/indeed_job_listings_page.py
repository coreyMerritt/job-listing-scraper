import logging
import time
from typing import List, Optional, Set
import psutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
  NoSuchElementException,
  StaleElementReferenceException,
  TimeoutException
)
from entities.indeed_job_listing import IndeedJobListing
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig
from models.enums.platform import Platform
from services.misc.database_manager import DatabaseManager
from services.misc.job_criteria_checker import JobCriteriaChecker
from services.misc.selenium_helper import SeleniumHelper
from services.misc.language_parser import LanguageParser


class IndeedJobListingsPage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __database_manager: DatabaseManager
  __language_parser: LanguageParser
  __criteria_checker: JobCriteriaChecker
  __quick_settings: QuickSettings
  __universal_config: UniversalConfig
  __current_session_jobs: Set[str]
  __current_page_number: int

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    database_manager: DatabaseManager,
    language_parser: LanguageParser,
    quick_settings: QuickSettings,
    universal_config: UniversalConfig
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__database_manager = database_manager
    self.__language_parser = language_parser
    self.__criteria_checker = JobCriteriaChecker()
    self.__quick_settings = quick_settings
    self.__universal_config = universal_config
    self.__current_session_jobs = set()
    self.__current_page_number = 1

  def is_present(self) -> bool:
    try:
      self.__get_job_listings_ul()
      return True
    except NoSuchElementException:
      return False

  def scrape_current_query(self) -> None:
    PROPER_JOB_INDEXES = [2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18]
    INVISIBLE_AD_INDEXES = [1, 13, 19]
    VISIBLE_AD_INDEXES = [7]
    LIS_PER_PAGE = len(PROPER_JOB_INDEXES) + len(INVISIBLE_AD_INDEXES) + len(VISIBLE_AD_INDEXES)
    i = 0
    while True:
      # Increment
      i += 1
      # Next Page and Auto-skips
      job_listing_li_index = (i % LIS_PER_PAGE) + 1
      JOB_IS_ON_NEXT_PAGE = i > 1 and job_listing_li_index == 1
      if JOB_IS_ON_NEXT_PAGE:
        if self.__is_a_next_page():
          self.__go_to_next_page()
        else:
          logging.info("End of Job Listings.")
          return
      elif job_listing_li_index in INVISIBLE_AD_INDEXES + VISIBLE_AD_INDEXES:
        logging.debug("Job Listing is an ad. Skipping...")
        continue  # Don't try to run against ads
      # Log
      logging.info("Attempting Job Listing: %s...", i)
      # Get Li, finished if cant
      job_listing_li = self.__get_job_listing_li(job_listing_li_index)
      if job_listing_li is None:
        logging.info("End of Job Listings.")
        return
      # TODO: Lets add some sort of validation that confirms that this is actually a job listing li
      # Scroll Li
      self.__selenium_helper.scroll_into_view(job_listing_li)
      # Make Brief
      brief_job_listing = self.__build_brief_job_listing(job_listing_li_index)
      # Skip potential ads
      if brief_job_listing is None:
        logging.debug("Skipping a fake Job Listing / advertisement...")
        continue
      # Print Brief
      brief_job_listing.print()
      # If already handled, next
      if brief_job_listing.to_minimal_str() in self.__current_session_jobs:
        logging.info("Ignoring Job Listing because: we've already applied this session.\n")
        continue
      # Add job to already handled
      self.__current_session_jobs.add(brief_job_listing.to_minimal_str())
      # Ensure job listing meets criteria
      if not self.__criteria_checker.passes(self.__quick_settings, self.__universal_config, brief_job_listing):
        logging.info("Ignoring Job Listing because it does not meet ignore/ideal criteria.")
        continue
      # If not full scrape, add to do and next
      if not self.__quick_settings.bot_behavior.full_scrape:
        self.__add_job_listing_to_db(brief_job_listing)
        continue
      # Click Li
      job_listing_li.click()
      # Make job listing, if unknown error, raise
      job_listing = self.__build_job_listing(job_listing_li_index)
      if job_listing is None:
        raise RuntimeError("Job listing is None -- unknown error case")
      # Ensure job listing meets criteria
      if not self.__criteria_checker.passes(self.__quick_settings, self.__universal_config, job_listing):
        logging.info("Ignoring Job Listing because it does not meet ignore/ideal criteria.")
        continue
      # Add to db
      self.__add_job_listing_to_db(job_listing)
      # Overload
      self.__handle_potential_overload()

  def __build_brief_job_listing(self, index: int, timeout=4.0) -> IndeedJobListing | None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_listing_li = self.__get_job_listing_li(index)
        if job_listing_li is None:
          return None
        self.__selenium_helper.scroll_into_view(job_listing_li)
        job_listing = IndeedJobListing(
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
    raise TimeoutException("Timed out trying to build brief job listing.")

  def __build_job_listing(self, index: int, timeout=4.0) -> IndeedJobListing | None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_listing_li = self.__get_job_listing_li(index)
        if job_listing_li is None:
          return None
        self.__selenium_helper.scroll_into_view(job_listing_li)
        job_description_html = self.__get_job_description_html()
        job_listing = IndeedJobListing(
          self.__language_parser,
          job_listing_li,
          job_description_html,
          self.__driver.current_url
        )
        return job_listing
      except StaleElementReferenceException:
        logging.warning("StaleElementReferenceException while trying to build job listing. Trying again...")
        time.sleep(0.1)
      except NoSuchElementException:
        logging.warning("NoSuchElementException while trying to build job listing. Trying again...")
        time.sleep(0.1)
    raise TimeoutException("Timed out trying to build job listing.")

  def __handle_potential_overload(self) -> None:
    current_memory_usage = psutil.virtual_memory().percent
    logging.debug("Current memory usage: %s%s", current_memory_usage, "%")
    if current_memory_usage > 90:
      print("\nCurrent memory usage is too high. Please clean up existing tabs to continue safely.")
      input("\tPress enter to proceed...")

  def __is_a_next_page(self) -> bool:
    visible_page_numbers = self.__get_visible_page_numbers()
    current_page_number = self.__get_current_page_number()
    if current_page_number + 1 in visible_page_numbers:
      return True
    return False

  def __go_to_next_page(self) -> None:
    logging.info("Going to page %s...", self.__current_page_number + 1)
    next_page_anchor = self.__get_next_page_anchor()
    try:
      next_page_anchor.click()
    except TimeoutException:
      logging.warning("Received a TimeoutException that has historically shown to not be an issue. Continuing...")
    self.__current_page_number += 1

  def __get_job_listing_li(self, index: int) -> Optional[WebElement]:
    try:
      job_listings_ul = self.__get_job_listings_ul()
      job_listing_li = job_listings_ul.find_element(By.XPATH, f"./li[{index}]")
      return job_listing_li
    except NoSuchElementException:
      return None

  def __get_job_listings_ul(self) -> WebElement:
    potential_job_listings_ul_xpaths = [
      "/html/body/main/div/div[2]/div/div[5]/div/div[1]/div[4]/div/ul",
      "/html/body/main/div/div/div[2]/div/div[5]/div/div[1]/div[4]/div/div/ul"
    ]
    for xpath in potential_job_listings_ul_xpaths:
      try:
        job_listings_ul = self.__driver.find_element(By.XPATH, xpath)
        return job_listings_ul
      except NoSuchElementException:
        pass
    raise NoSuchElementException("Failed to find Job Listings ul.")

  def __get_next_page_anchor(self) -> WebElement:
    page_buttons_ul = self.__get_page_buttons_ul()
    current_page_number = self.__get_current_page_number()
    for i in range(1, 7):
      potential_relative_next_page_anchor_xpath = f"./li[{i}]/a[1]"
      potential_next_page_anchor = page_buttons_ul.find_element(By.XPATH, potential_relative_next_page_anchor_xpath)
      potential_next_page_anchor_text = potential_next_page_anchor.text
      if potential_next_page_anchor_text:
        if potential_next_page_anchor_text == str(current_page_number + 1):
          return potential_next_page_anchor
    raise NoSuchElementException("Failed to find next page anchor.")

  def __get_visible_page_numbers(self) -> List[int]:
    page_buttons_ul = self.__get_page_buttons_ul()
    visible_page_numbers = []
    for i in range(1, 6):
      relative_anchor_xpath = f"./li[{i}]/a[1]"
      try:
        page_anchor = page_buttons_ul.find_element(By.XPATH, relative_anchor_xpath)
      except NoSuchElementException:
        continue
      page_anchor_text = page_anchor.text
      if page_anchor_text:
        visible_page_numbers.append(int(page_anchor_text))
    return visible_page_numbers

  def __get_current_page_number(self) -> int:
    return self.__current_page_number

  def __get_page_buttons_ul(self, timeout=5) -> WebElement:
    potential_page_buttons_ul_xpaths = [
      "/html/body/main/div/div[2]/div/div[5]/div/div[1]/nav/ul",
      "/html/body/main/div/div/div[2]/div/div[5]/div/div[1]/nav/ul"
    ]
    start_time = time.time()
    while time.time() - start_time < timeout:
      for xpath in potential_page_buttons_ul_xpaths:
        try:
          page_buttons_ul = self.__driver.find_element(By.XPATH, xpath)
          return page_buttons_ul
        except NoSuchElementException:
          logging.debug("Failed to find page buttons ul. Trying again...")
          time.sleep(0.1)
    raise NoSuchElementException("Failed to find page buttons ul.")

  def __get_job_listing_anchor(self, job_listing_li: WebElement) -> WebElement:
    relative_job_listing_anchor_xpath = "./div/div/div/div/div/div/table/tbody/tr/td/div[1]/h2/a"
    job_listing_anchor = job_listing_li.find_element(By.XPATH, relative_job_listing_anchor_xpath)
    return job_listing_anchor

  def __get_job_description_html(self, timeout=30) -> str:
    job_description_id = "jobDescriptionText"
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_description_div = self.__driver.find_element(By.ID, job_description_id)
        break
      except NoSuchElementException:
        logging.debug("Failed to get job description div. Trying again...")
        time.sleep(0.5)
    job_description_html = job_description_div.get_attribute("innerHTML")
    if job_description_html:
      return job_description_html
    raise AttributeError("Job description div has no innerHTML attribute.")

  def __add_job_listing_to_db(self, job_listing: IndeedJobListing) -> None:
    self.__database_manager.create_new_job_listing(
      job_listing,
      Platform.INDEED
    )
