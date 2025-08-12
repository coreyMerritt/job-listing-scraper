import logging
import re
import time
from typing import Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
  ElementClickInterceptedException,
  ElementNotInteractableException,
  JavascriptException,
  NoSuchElementException,
  StaleElementReferenceException,
  TimeoutException
)
from entities.job_listings.glassdoor_job_listing import GlassdoorJobListing
from exceptions.glassdoor_zero_jobs_bug_exception import GlassdoorZeroJobsBugException
from exceptions.job_details_didnt_load_exception import JobDetailsDidntLoadException
from exceptions.job_listing_is_advertisement_exception import JobListingIsAdvertisementException
from exceptions.job_listing_opens_in_window_exception import JobListingOpensInWindowException
from exceptions.no_more_job_listings_exception import NoMoreJobListingsException
from exceptions.no_next_page_exception import NoNextPageException
from exceptions.no_results_found_page_exception import NoResultsFoundPageException
from exceptions.page_didnt_load_exception import PageDidntLoadException
from exceptions.page_froze_exception import PageFrozeException
from exceptions.unable_to_determine_job_count_exception import UnableToDetermineJobCountException
from models.enums.element_type import ElementType
from models.enums.platform import Platform
from services.pages.job_listing_pages.abc_job_listings_page import JobListingsPage


class GlassdoorJobListingsPage(JobListingsPage):
  def _is_zero_results(self, timeout=10.0) -> bool:
    search_results_class = "SearchResultsHeader_jobCount__eHngv"
    start_time = time.time()
    while time.time() - start_time < timeout:
      if self.__is_create_job_dialog():
        self.__remove_create_job_dialog()
      if self.__is_survey_popup():
        self.__remove_survey_popup()
      try:
        search_results_h1 = self._driver.find_element(By.CLASS_NAME, search_results_class)
        search_results_text = search_results_h1.text.lower().replace(",", "").strip()
        search_results_regex = re.match(r"^([0-9]+) .+", search_results_text)
        assert search_results_regex
        search_results_job_count = search_results_regex.group(1)
        logging.debug("Found %s results.", search_results_job_count)
        if search_results_job_count == "0":
          return True
        return False
      except NoSuchElementException:
        logging.debug("NoSuchElementException. Trying again...")  # TODO: Improve msg
        time.sleep(0.1)
    raise UnableToDetermineJobCountException()

  def _handle_incrementors(self, total_jobs_tried: int, job_listing_li_index: int) -> Tuple[int, int]:
    total_jobs_tried += 1
    job_listing_li_index = total_jobs_tried
    return (total_jobs_tried, job_listing_li_index)

  def _get_job_listing_li(self, job_listing_li_index: int, timeout=10.0) -> WebElement:
    job_listings_ul = self.__get_job_listings_ul()
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_listing_li = job_listings_ul.find_element(By.XPATH, f"./li[{job_listing_li_index}]")
        if self.__is_advertisement(job_listing_li):
          raise JobListingIsAdvertisementException()
        return job_listing_li
      except ElementClickInterceptedException:
        logging.debug("ElementClickInterceptedException. Attempting to remove popups and trying again...")
        if self.__is_create_job_dialog():
          self.__remove_create_job_dialog()
        if self.__is_survey_popup():
          self.__remove_survey_popup()
      except NoSuchElementException as e:
        raise NoMoreJobListingsException() from e
      except StaleElementReferenceException:
        logging.debug("Failed to get Job Listing li. Trying again...")
        job_listings_ul = self.__get_job_listings_ul()
    raise NoMoreJobListingsException()

  def _build_brief_job_listing(self, job_listing_li: WebElement, timeout=10.0) -> GlassdoorJobListing:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        self._selenium_helper.scroll_into_view(job_listing_li)
        brief_job_listing = GlassdoorJobListing(
          self._language_parser,
          job_listing_li
        )
        return brief_job_listing
      except TimeoutError:
        logging.warning("TimeoutError while trying to build job listing. Trying again...")
        time.sleep(0.1)
    raise TimeoutException("Timed out trying to build job listing.")

  def _build_job_listing(
    self,
    job_listing_li: WebElement,
    job_details_div: WebElement,
    timeout=10.0
  ) -> GlassdoorJobListing:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        self._get_job_details_div()
        self._selenium_helper.scroll_into_view(job_listing_li)
        job_listing = GlassdoorJobListing(
          self._language_parser,
          job_listing_li,
          job_details_div
        )
        return job_listing
      except StaleElementReferenceException:
        if not self.__job_details_div_is_present():
          if self.__page_didnt_load_is_present():
            self.__reload_job_description()
        logging.warning("StaleElementReferenceException while trying to build job listing. Trying again...")
        time.sleep(0.1)
      except NoSuchElementException:
        logging.warning("NoSuchElementException while trying to build job listing. Trying again...")
        time.sleep(0.1)
      except TimeoutError:
        logging.warning("TimeoutError while trying to build job listing. Trying again...")
        time.sleep(0.1)
    raise TimeoutException("Timed out trying to build job listing.")

  def _add_job_listing_to_db(self, job_listing: GlassdoorJobListing) -> None:
    self._database_manager.create_new_job_listing(
      job_listing,
      Platform.GLASSDOOR
    )

  def _anti_rate_limit_wait(self) -> None:
    pass

  def _click_job(self, job_listing_li: WebElement, timeout=10) -> None:
    try:
      if self.__is_create_job_dialog():
        self.__remove_create_job_dialog()
      if self.__is_survey_popup():
        self.__remove_survey_popup()
      start_tab_count = len(self._driver.window_handles)
      job_listing_li.click()
      if "/job-listing/" in self._driver.current_url:
        raise JobListingOpensInWindowException()
      if len(self._driver.window_handles) > start_tab_count:
        raise JobListingOpensInWindowException()
    except ElementClickInterceptedException as e:
      raise PageFrozeException() from e

  def _get_job_details_div(self, timeout=10.0) -> WebElement:
    self.__wait_for_job_details_div(timeout)
    job_details_div_xpath = "/html/body/div[4]/div[4]/div[2]/div[2]/div/div[1]"
    job_details_div = self._driver.find_element(By.XPATH, job_details_div_xpath)
    return job_details_div

  def _need_next_page(self, job_listing_li_index: int) -> bool:
    return self._is_next_page()

  def _is_next_page(self) -> bool:
    self._selenium_helper.scroll_to_bottom()
    try:
      job_listings_ul = self.__get_job_listings_ul()
      job_listings_ul.find_element(By.XPATH, "../div/div/button")
      return True
    except NoSuchElementException:
      return False

  def _go_to_next_page(self, timeout=15.0) -> None:
    while self._is_next_page():
      try:
        no_jobs_regex = r"^0 .+ Jobs in .+"
        assert not re.search(no_jobs_regex, self._driver.title)
        starting_li_count = len(self.__get_job_listings_ul().find_elements(By.TAG_NAME, "li"))
        show_more_jobs_button = self.__get_show_more_jobs_button()
        show_more_jobs_button.click()
        self.__wait_for_more_job_listings(starting_li_count)
        if re.search(no_jobs_regex, self._driver.title):
          raise GlassdoorZeroJobsBugException()
      except ElementNotInteractableException:
        logging.debug("ElementNotInteractableException. Checking for dialogs and trying again...")
        if self.__is_create_job_dialog():
          self.__remove_create_job_dialog()
        if self.__is_survey_popup():
          self.__remove_survey_popup()
        time.sleep(0.1)
      except ElementClickInterceptedException:
        logging.debug("ElementClickInterceptedException. Checking for dialogs and trying again...")
        if self.__is_create_job_dialog():
          self.__remove_create_job_dialog()
        if self.__is_survey_popup():
          self.__remove_survey_popup()
        time.sleep(0.1)
      except StaleElementReferenceException:
        self.__get_show_more_jobs_button()
        time.sleep(0.1)



  def __get_job_listings_ul(self) -> WebElement:
    try:
      job_listings_ul = self._selenium_helper.get_element_by_aria_label("Jobs List")
    except ElementClickInterceptedException:
      if self.__is_create_job_dialog():
        self.__remove_create_job_dialog()
      if self.__is_survey_popup():
        self.__remove_survey_popup()
      job_listings_ul = self._selenium_helper.get_element_by_aria_label("Jobs List")
    except NoSuchElementException as e:
      if self.__page_didnt_load_is_present():
        raise PageDidntLoadException() from e
      if self.__is_create_job_dialog():
        self.__remove_create_job_dialog()
      if self.__is_survey_popup():
        self.__remove_survey_popup()
      if self.__is_no_results_found_page():
        raise NoResultsFoundPageException() from e
      job_listings_ul = self._selenium_helper.get_element_by_aria_label("Jobs List")
    return job_listings_ul

  def __is_advertisement(self, job_listing_li: WebElement) -> bool:
    job_listing_li_class = job_listing_li.get_attribute("class")
    if job_listing_li_class == "ForYouNudgeCard_cardWrapper__bkg9g":
      return True
    return False

  def __is_create_job_dialog(self) -> bool:
    create_job_alert_dialog_xpath = "/html/body/div[8]/div/dialog"
    relative_cancel_dialog_button_xpath = "./div[2]/div[1]/div[1]/button[1]"
    try:
      create_job_alert_dialog = self._driver.find_element(By.XPATH, create_job_alert_dialog_xpath)
      create_job_alert_dialog.find_element(By.XPATH, relative_cancel_dialog_button_xpath)
      return True
    except NoSuchElementException:
      return False

  def __remove_create_job_dialog(self) -> None:
    logging.debug("Removing create job dialog...")
    create_job_alert_dialog_xpath = "/html/body/div[8]/div/dialog"
    relative_cancel_dialog_button_xpath = "./div[2]/div[1]/div[1]/button[1]"
    create_job_alert_dialog = self._driver.find_element(By.XPATH, create_job_alert_dialog_xpath)
    cancel_button = create_job_alert_dialog.find_element(By.XPATH, relative_cancel_dialog_button_xpath)
    cancel_button.click()

  def __is_survey_popup(self) -> bool:
    exit_button_id = "qual_close_open"
    try:
      self._driver.find_element(By.ID, exit_button_id)
      return True
    except NoSuchElementException:
      return False

  def __remove_survey_popup(self) -> None:
    exit_button_id = "qual_close_open"
    exit_button = self._driver.find_element(By.ID, exit_button_id)
    exit_button.click()

  def __is_no_results_found_page(self) -> bool:
    no_results_found_h1_class = "ErrorPage_errorPageTitle__XtznY"
    try:
      self._driver.find_element(By.CLASS_NAME, no_results_found_h1_class)
      return True
    except NoSuchElementException:
      return False

  def __job_details_div_is_present(self) -> bool:
    job_details_div_xpath = "/html/body/div[4]/div[4]/div[2]/div[2]/div/div[1]"
    try:
      self._driver.find_element(By.XPATH, job_details_div_xpath)
      return True
    except NoSuchElementException:
      return False

  def __page_didnt_load_is_present(self) -> bool:
    return self._selenium_helper.exact_text_is_present("Zzzzzzzz...", ElementType.H1)

  def __reload_job_description(self) -> None:
    try_again_span = self._selenium_helper.get_element_by_exact_text("Try again", ElementType.SPAN)
    parent_span = try_again_span.find_element(By.XPATH, "..")
    try_again_button = parent_span.find_element(By.XPATH, "..")
    try_again_button.click()
    self.__wait_for_job_details_div()

  def __get_show_more_jobs_button(self, timeout=10.0) -> WebElement:
    if not self._is_next_page():
      raise NoNextPageException()
    self._selenium_helper.scroll_to_bottom()
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_listings_ul = self.__get_job_listings_ul()
        show_more_jobs_button = job_listings_ul.find_element(By.XPATH, "../div/div/button")
        return show_more_jobs_button
      except NoSuchElementException:
        logging.debug("Waiting for show more jobs button...")
        time.sleep(0.1)
    raise TimeoutException("Timed out waiting for show more jobs button.")

  def __wait_for_more_job_listings(self, starting_li_count: int) -> None:
    confirm_more_job_listings_timeout = 10.0
    start_time = time.time()
    while time.time() - start_time < confirm_more_job_listings_timeout:
      ending_li_count = len(self.__get_job_listings_ul().find_elements(By.TAG_NAME, "li"))
      if starting_li_count != ending_li_count:
        break
    if starting_li_count == ending_li_count:
      if self._is_next_page():
        raise JavascriptException("Button did not produce more <li>s")

  def __wait_for_job_details_div(self, timeout=10.0) -> None:
    start_time = time.time()
    while time.time() - start_time < timeout:
      try:
        job_details_div_xpath = "/html/body/div[4]/div[4]/div[2]/div[2]/div/div[1]"
        job_details_div = self._driver.find_element(By.XPATH, job_details_div_xpath)
        job_details_html = job_details_div.get_attribute("innerHTML")
        if not job_details_html:
          logging.debug("Waiting for job description to load... [HTML]")
          time.sleep(0.1)
          continue
        if not len(job_details_html) > 100:
          logging.debug("Waiting for job description to load... [LEN]")
          time.sleep(0.1)
          continue
        if not "Show more" in job_details_html:
          logging.debug("Waiting for job description to load... [SHOW MORE]")
          time.sleep(0.1)
          continue
        return
      except NoSuchElementException:
        logging.debug("Waiting for job description to load... [NOSUCHELE]")
        time.sleep(0.1)
    raise JobDetailsDidntLoadException()
