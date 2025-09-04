import logging
import time
from typing import List, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
  ElementClickInterceptedException,
  NoSuchElementException,
  StaleElementReferenceException,
  TimeoutException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from entities.job_listings.abc_job_listing import JobListing
from entities.job_listings.indeed_job_listing import IndeedJobListing
from exceptions.job_listing_is_advertisement_exception import JobListingIsAdvertisementException
from exceptions.job_listing_opens_in_window_exception import JobListingOpensInWindowException
from exceptions.no_more_job_listings_exception import NoMoreJobListingsException
from models.enums.element_type import ElementType
from models.enums.platform import Platform
from services.pages.job_listing_pages.abc_job_listings_page import JobListingsPage


class IndeedJobListingsPage(JobListingsPage):
  def is_present(self) -> bool:
    try:
      self._get_job_listings_ul()
      return True
    except NoSuchElementException:
      return False

  def _get_base_url(self) -> str:
    return "indeed.com"

  def _get_platform(self) -> Platform:
    return Platform.INDEED

  def _is_zero_results(self, timeout=10.0) -> bool:
    return False  # TODO

  def _handle_incrementors(self, total_jobs_tried: int, job_listing_li_index: int) -> Tuple[int, int]:
    total_jobs_tried += 1
    job_listing_li_index = (total_jobs_tried % 20) + 1
    if job_listing_li_index == 1:
      total_jobs_tried += 1
      job_listing_li_index = (total_jobs_tried % 20) + 1
    return total_jobs_tried, job_listing_li_index

  def _get_job_listing_li(self, job_listing_li_index: int, timeout=10.0) -> WebElement:
    job_listings_ul = self._get_job_listings_ul()
    try:
      job_listing_li = job_listings_ul.find_element(By.XPATH, f"./li[{job_listing_li_index}]")
    except NoSuchElementException as e:
      raise NoMoreJobListingsException() from e
    ADVERTISEMENT_MATCHES = [
      "mosaic-afterFifthJobResult",
      "mosaic-afterTenthJobResult",
      "mosaicZone_afterFifteenthJobResult"
      "jobsearch-SerpJobCard--sponsored",
      "icl-JobResult-card--sponsored"
    ]
    job_listing_html = job_listing_li.get_attribute("innerHTML")
    if job_listing_html:
      for phrase in ADVERTISEMENT_MATCHES:
        if phrase in job_listing_html:
          raise JobListingIsAdvertisementException()
    try:
      card_outline = job_listing_li.find_element(By.CSS_SELECTOR, "div.cardOutline")
      if card_outline.get_attribute("aria-hidden") == "true":
        raise JobListingIsAdvertisementException()
    except NoSuchElementException as e:
      raise JobListingIsAdvertisementException() from e
    return job_listing_li

  def _build_brief_job_listing(self, job_listing_li: WebElement, timeout=30.0) -> IndeedJobListing | None:
    try:
      self._selenium_helper.scroll_into_view(job_listing_li)
      job_listing = IndeedJobListing(
        self._language_parser,
        job_listing_li
      )
      return job_listing
    except NoSuchElementException as e:
      raise NoMoreJobListingsException from e

  def _add_job_listing_to_db(self, job_listing: IndeedJobListing) -> None:
    self._database_manager.create_new_job_listing(
      job_listing,
      Platform.INDEED
    )

  def _anti_rate_limit_wait(self) -> None:
    pass

  def _click_job(self, job_listing_li: WebElement, timeout=10.0) -> None:
    WebDriverWait(self._driver, timeout).until(
      EC.element_to_be_clickable(job_listing_li)
    )
    try:
      job_listing_li.click()
    except ElementClickInterceptedException as e:
      if self.__is_tos_update_window():
        self.__accept_tos_update()
        job_listing_li.click()
      else:
        raise e

  def _get_job_details_div(self, timeout=30.0) -> WebElement:
    job_details_div_id = "jobDescriptionText"
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_description_div = self._driver.find_element(By.ID, job_details_div_id)
        return job_description_div
      except NoSuchElementException as e:
        if "indeed.com/viewjob" in self._driver.current_url:
          raise JobListingOpensInWindowException() from e
        logging.debug("Failed to get job description div. Trying again...")
        time.sleep(0.5)
    if "indeed.com/viewjob" in self._driver.current_url:
      raise JobListingOpensInWindowException()
    if not self.__is_additional_verification_required_page():
      raise AttributeError("Job description div has no innerHTML attribute.")
    while self.__is_additional_verification_required_page():
      logging.debug("Waiting for user to handle security checkpoint...")
      time.sleep(1)
    return self._get_job_details_div()

  def _build_job_listing(self, job_listing_li: WebElement, job_details_div: WebElement, timeout=10.0) -> JobListing:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_listing = IndeedJobListing(
          self._language_parser,
          job_listing_li,
          job_details_div
        )
        return job_listing
      except StaleElementReferenceException as e:
        if "indeed.com/viewjob" in self._driver.current_url:
          raise JobListingOpensInWindowException() from e
        raise e
      except NoSuchElementException:
        logging.warning("NoSuchElementException while trying to build job listing. Trying again...")
        time.sleep(0.1)
    if "indeed.com/viewjob" in self._driver.current_url:
      raise JobListingOpensInWindowException()
    raise TimeoutException("Timed out trying to build job listing.")

  def _need_next_page(self, job_listing_li_index: int) -> bool:
    return job_listing_li_index == 2

  def _is_next_page(self) -> bool:
    visible_page_numbers = self.__get_visible_page_numbers()
    current_page_number = self.__get_current_page_number()
    if current_page_number + 1 in visible_page_numbers:
      return True
    return False

  def _go_to_next_page(self) -> None:
    next_page_anchor = self.__get_next_page_anchor()
    try:
      next_page_anchor.click()
    except TimeoutException:
      logging.warning("Received a TimeoutException that has historgit sically shown to not be an issue. Continuing...")

  def _get_job_listings_ul(self, timeout=5.0) -> WebElement:
    last_error = None
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        toast_div_id = "toast"
        toast_div = self._driver.find_element(By.ID, toast_div_id)
        job_listings_ul = toast_div.find_element(By.XPATH, "../ul")
        return job_listings_ul
      except NoSuchElementException as e:
        if "/viewjob" in self._driver.current_url:
          raise JobListingOpensInWindowException() from e
        last_error = e
        logging.warning("Failed to find job listings ul. Trying again...")
        time.sleep(0.1)
    if last_error:
      raise last_error
    raise RuntimeError("Unknown error occured while trying to get job listings ul.")

  def __get_current_page_number(self) -> int:
    page_buttons_ul = self.__get_page_buttons_ul()
    for i in range(1, 7):
      potential_relative_next_page_anchor_xpath = f"./li[{i}]/a[1]"
      potential_next_page_anchor = page_buttons_ul.find_element(By.XPATH, potential_relative_next_page_anchor_xpath)
      potential_next_page_data_test_id = potential_next_page_anchor.get_attribute("data-testid")
      if potential_next_page_data_test_id:
        if potential_next_page_data_test_id == "pagination-page-current":
          current_page_anchor_text = potential_next_page_anchor.text
          if current_page_anchor_text:
            return int(current_page_anchor_text)
    raise RuntimeError("Failed to find next page anchor.")

  def __get_next_page_anchor(self) -> WebElement:
    page_buttons_ul = self.__get_page_buttons_ul()
    found_current_page = False
    for i in range(1, 7):
      potential_relative_next_page_anchor_xpath = f"./li[{i}]/a[1]"
      potential_next_page_anchor = page_buttons_ul.find_element(By.XPATH, potential_relative_next_page_anchor_xpath)
      potential_next_page_data_test_id = potential_next_page_anchor.get_attribute("data-testid")
      if potential_next_page_data_test_id:
        if potential_next_page_data_test_id == "pagination-page-current":
          found_current_page = True
          continue
      if found_current_page:
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

  def __get_page_buttons_ul(self, timeout=5.0) -> WebElement:
    potential_page_buttons_ul_xpaths = [
      "/html/body/main/div/div[2]/div/div[5]/div/div[1]/nav/ul",
      "/html/body/main/div/div/div[2]/div/div[5]/div/div[1]/nav/ul"
    ]
    start_time = time.time()
    while time.time() - start_time < timeout:
      for xpath in potential_page_buttons_ul_xpaths:
        try:
          page_buttons_ul = self._driver.find_element(By.XPATH, xpath)
          return page_buttons_ul
        except NoSuchElementException:
          logging.debug("Failed to find page buttons ul. Trying again...")
          time.sleep(0.1)
    raise NoSuchElementException("Failed to find page buttons ul.")

  def __is_additional_verification_required_page(self) -> bool:
    return self._selenium_helper.exact_text_is_present(
      "Additional Verification Required",
      ElementType.H1
    )

  def __is_tos_update_window(self) -> bool:
    tos_update_window_id = ":r0:"
    try:
      self._driver.find_element(By.ID, tos_update_window_id)
      return True
    except NoSuchElementException:
      return False

  def __accept_tos_update(self) -> None:
    assert self.__is_tos_update_window()
    tos_update_window_id = ":r0:"
    tos_update_window = self._driver.find_element(By.ID, tos_update_window_id)
    accept_terms_button = self._selenium_helper.get_element_by_exact_text(
      "Accept Terms",
      ElementType.BUTTON,
      tos_update_window
    )
    accept_terms_button.click()
