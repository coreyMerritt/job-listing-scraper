from abc import abstractmethod
import logging
import random
import time
from typing import Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
  ElementClickInterceptedException,
  NoSuchElementException,
  TimeoutException
)
from entities.job_listings.abc_job_listing import JobListing
from exceptions.job_details_didnt_load_exception import JobDetailsDidntLoadException
from exceptions.no_more_job_listings_exception import NoMoreJobListingsException
from exceptions.rate_limited_exception import RateLimitedException
from exceptions.something_went_wrong_page_exception import SomethingWentWrongPageException
from exceptions.zero_search_results_exception import ZeroSearchResultsException
from models.enums.element_type import ElementType
from models.enums.platform import Platform
from services.pages.job_listing_pages.abc_job_listings_page import JobListingsPage


class LinkedinJobListingsPage(JobListingsPage):
  @abstractmethod
  def is_present(self) -> bool:
    pass

  @abstractmethod
  def _is_zero_results(self, timeout=10.0) -> bool:
    pass

  @abstractmethod
  def _build_brief_job_listing(self, job_listing_li: WebElement, timeout=4.0) -> JobListing:
    pass

  @abstractmethod
  def _build_job_listing(self, job_listing_li: WebElement, job_details_div: WebElement, timeout=10.0) -> JobListing:
    pass

  @abstractmethod
  def _get_job_listings_ul(self, timeout=5.0) -> WebElement:
    pass

  @abstractmethod
  def _job_listing_li_is_active(self, job_listing_li: WebElement) -> bool:
    pass

  def _get_platform(self) -> Platform:
    return Platform.LINKEDIN

  def _handle_incrementors(self, total_jobs_tried: int, job_listing_li_index: int) -> Tuple[int, int]:
    total_jobs_tried += 1
    if total_jobs_tried >= 4:
      self._selenium_helper.scroll_down(self._get_job_listings_ul())
    job_listing_li_index = total_jobs_tried % 26
    if job_listing_li_index == 0:
      total_jobs_tried += 1
      job_listing_li_index = 1
    return (total_jobs_tried, job_listing_li_index)

  def _get_job_listing_li(self, job_listing_li_index: int, timeout=10.0) -> WebElement:
    relative_job_listing_li_xpath = f"./li[{job_listing_li_index}]"
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_listings_ul = self._get_job_listings_ul()
        job_listing_li = job_listings_ul.find_element(By.XPATH, relative_job_listing_li_xpath)
        return job_listing_li
      except NoSuchElementException:
        logging.debug("Failed to find Job Listing Li. Trying again...")
        time.sleep(0.1)
      except TimeoutException as e:
        raise SomethingWentWrongPageException() from e
    raise NoMoreJobListingsException()

  def _add_job_listing_to_db(self, job_listing: JobListing) -> None:
    self._database_manager.create_new_job_listing(
      job_listing,
      Platform.LINKEDIN
    )

  def _anti_rate_limit_wait(self) -> None:
    random_time = random.random() * 5
    time.sleep(random_time)

  def _click_job(self, job_listing_li: WebElement, timeout=10.0) -> None:
    self._selenium_helper.scroll_into_view(job_listing_li)
    self.__click_job_listing_li(job_listing_li)
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self._job_listing_li_is_active(job_listing_li):
        return
      logging.debug("Waiting for Job Listing li to be active to confirm Job Listing click...")
      time.sleep(0.1)
    raise TimeoutError("Timed out waiting for full Job Listing to load.")

  def _get_job_details_div(self, timeout=30.0) -> WebElement:
    job_details_div_selector = "div.jobs-description-content__text--stretch"
    start_time = time.time()
    job_listing_is_loading = False
    while time.time() - start_time < timeout:
      try:
        job_details_div = self._driver.find_element(By.CSS_SELECTOR, job_details_div_selector)
        job_details_html = job_details_div.get_attribute("innerHTML")
        if not job_details_html:
          job_listing_is_loading = True
          continue
        if len(job_details_html) < 100:
          job_listing_is_loading = True
          continue
        return job_details_div
      except NoSuchElementException:
        logging.info("Waiting for job description content div...")
        time.sleep(0.1)
    if job_listing_is_loading:
      raise JobDetailsDidntLoadException()
    raise TimeoutException("Timed out waiting for job description content div.")

  def _need_next_page(self, job_listing_li_index: int) -> bool:
    return job_listing_li_index == 1

  def _is_next_page(self) -> bool:
    main_content_div = self.__get_main_content_div()
    return self._selenium_helper.exact_aria_label_is_present(
      "View next page",
      base_element=main_content_div
    )

  def _go_to_next_page(self) -> None:
    main_content_div = self.__get_main_content_div()
    next_page_span = self._selenium_helper.get_element_by_aria_label(
      "View next page",
      base_element=main_content_div
    )
    next_page_span.click()

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

  def __get_main_content_div(self) -> WebElement | None:
    main_content_div_id = "main"
    return self._driver.find_element(By.ID, main_content_div_id)

  def __is_no_matching_jobs_page(self) -> bool:
    return self._selenium_helper.exact_text_is_present(
      "No matching jobs found",
      ElementType.H2
    )

  def __handle_potential_problems(self) -> None:
    if self.__is_job_safety_reminder_popup():
      self.__remove_job_search_safety_reminder_popup()
    elif self.__is_something_went_wrong_div():
      self._driver.refresh()
      time.sleep(5)   # It seems that if you don't wait here, the issue will arise again -- likely rate limiting
    elif self.__is_rate_limited_page():
      raise RateLimitedException(Platform.LINKEDIN)
    elif self.__is_no_matching_jobs_page():
      raise ZeroSearchResultsException()

  def __is_something_went_wrong_div(self) -> bool:
    return self._selenium_helper.exact_text_is_present(
      "Something went wrong",
      ElementType.H2
    )

  def __is_job_safety_reminder_popup(self) -> bool:
    return self._selenium_helper.exact_text_is_present(
      "Job search safety reminder",
      ElementType.H2
    )

  def __remove_job_search_safety_reminder_popup(self) -> None:
    assert self.__is_job_safety_reminder_popup()
    continue_applying_button_id = "jobs-apply-button-id"
    continue_applying_button = self._driver.find_element(By.ID, continue_applying_button_id)
    continue_applying_button.click()

  def __is_rate_limited_page(self) -> bool:
    error_code_div_class = "error-code"
    try:
      self._driver.find_element(By.CLASS_NAME, error_code_div_class)
      return True
    except NoSuchElementException:
      return False
