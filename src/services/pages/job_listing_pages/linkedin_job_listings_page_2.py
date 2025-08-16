import logging
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
  NoSuchElementException,
  StaleElementReferenceException,
  TimeoutException
)
from entities.job_listings.linkedin_job_listing_2 import LinkedinJobListing2
from exceptions.linkedin_something_went_wrong_div_exception import LinkedinSomethingWentWrongException
from exceptions.no_results_data_exception import NoResultsDataException
from exceptions.rate_limited_exception import RateLimitedException
from models.enums.platform import Platform
from services.pages.job_listing_pages.linkedin_job_listings_page_1 import LinkedinJobListingsPage


class LinkedinJobListingsPage2(LinkedinJobListingsPage):
  def is_present(self) -> bool:
    results_div_selector = ".jobs-search-results-list__subtitle"
    try:
      self._driver.find_element(By.CSS_SELECTOR, results_div_selector)
      return True
    except NoSuchElementException:
      return False

  def _is_zero_results(self, timeout=30.0) -> bool:
    results_div_selector = ".jobs-search-results-list__subtitle"
    results_regex = r"([0-9]+)\ result"
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        results_div = self._driver.find_element(By.CSS_SELECTOR, results_div_selector)
        results_span = results_div.find_element(By.XPATH, "./span")
        results_text = results_span.text
        if results_text:
          match = re.search(results_regex, results_text)
          if match:
            group = match.group(1)
            results = int(group)
            if results == 0:
              return True
            return False
      except NoSuchElementException as e:
        if self.__is_rate_limited_page():
          raise RateLimitedException(Platform.LINKEDIN) from e
        logging.debug("Failed to find results div. Trying again...")
        time.sleep(0.1)
    raise NoResultsDataException("Failed to find results div.")

  def _get_job_listings_ul(self, timeout=5.0) -> WebElement:
    logging.debug("Getting Job Listings ul...")
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_listings_ul_class = "EIBJhHUoVSorgyXUsQxzcVWEyDnMiJeHpPihjQ"
        job_listings_ul = self._driver.find_element(By.CLASS_NAME, job_listings_ul_class)
        return job_listings_ul
      except NoSuchElementException:
        logging.debug("Waiting for Job Listings ul...")
        time.sleep(0.1)
      except StaleElementReferenceException:
        logging.debug("Waiting for Job Listings ul...")
        time.sleep(0.1)
    raise TimeoutException("Timed out trying to get job listings ul.")

  def _build_brief_job_listing(self, job_listing_li: WebElement, timeout=4.0) -> LinkedinJobListing2:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        self._selenium_helper.scroll_into_view(job_listing_li)
        job_listing = LinkedinJobListing2(
          self._language_parser,
          job_listing_li
        )
        return job_listing
      except NoSuchElementException:
        logging.warning("NoSuchElementException while trying to build brief job listing. Trying again...")
        time.sleep(0.1)
    raise NoSuchElementException("Failed to find full job details div.")

  def _build_job_listing(
    self,
    job_listing_li: WebElement,
    job_details_div: WebElement,
    timeout=10
  ) -> LinkedinJobListing2:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        self._selenium_helper.scroll_into_view(job_listing_li)
        job_header_div = self.__get_job_header_div()
        job_listing = LinkedinJobListing2(
          self._language_parser,
          job_listing_li,
          job_details_div,
          job_header_div
        )
        return job_listing
      except NoSuchElementException:
        logging.warning("NoSuchElementException while trying to build job listing. Trying again...")
        time.sleep(0.1)
    if self.__is_something_went_wrong_div():
      raise LinkedinSomethingWentWrongException()
    raise NoSuchElementException("Failed to find full job details div.")

  def _job_listing_li_is_active(self, job_listing_li: WebElement) -> bool:
    activity_div = job_listing_li.find_element(By.XPATH, "./div/div")
    active_class = "active"
    current_classes = activity_div.get_attribute("class")
    assert current_classes
    return active_class in current_classes

  def __get_job_header_div(self) -> WebElement:
    job_header_selector = ".relative.job-details-jobs-unified-top-card__container--two-pane"
    job_header = self._driver.find_element(By.CSS_SELECTOR, job_header_selector)
    return job_header

  def __is_rate_limited_page(self) -> bool:
    error_code_div_class = "error-code"
    try:
      self._driver.find_element(By.CLASS_NAME, error_code_div_class)
      return True
    except NoSuchElementException:
      return False
