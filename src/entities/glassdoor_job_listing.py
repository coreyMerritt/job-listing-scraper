import logging
import re
import time
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from entities.abc_job_listing import JobListing
from services.misc.language_parser import LanguageParser


class GlassdoorJobListing(JobListing):
  __url: str | None
  __job_listing_li: WebElement
  __job_info_div: WebElement | None

  def __init__(
    self,
    language_parser: LanguageParser,
    job_listing_li: WebElement,
    job_info_div: WebElement | None = None,
    url: str | None = None
  ):
    self.__url = url
    self.__job_listing_li = job_listing_li
    self.__job_info_div = job_info_div
    super().__init__(language_parser)

  # TODO: Implement
  def _init_min_pay(self) -> None:
    self.set_min_pay(None)

  # TODO: Implement
  def _init_max_pay(self) -> None:
    self.set_max_pay(None)

  def _init_title(self) -> None:
    job_title_anchor_class = "JobCard_jobTitle__GLyJ1"
    job_title_anchor = self.__job_listing_li.find_element(By.CLASS_NAME, job_title_anchor_class)
    self.set_title(job_title_anchor.text.strip())

  def _init_company(self) -> None:
    company_span_class = "EmployerProfile_compactEmployerName__9MGcV"
    company_span = self.__job_listing_li.find_element(By.CLASS_NAME, company_span_class)
    self.set_company(company_span.text.strip())

  def _init_location(self) -> None:
    location_div_class = "JobCard_location__Ds1fM"
    location_div = self.__job_listing_li.find_element(By.CLASS_NAME, location_div_class)
    self.set_location(location_div.text.strip())

  def _init_url(self) -> None:
    if self.__url:
      self.set_url(self.__url)
    else:
      job_anchor_class = "JobCard_trackingLink__HMyun"
      job_anchor = self.__job_listing_li.find_element(By.CLASS_NAME, job_anchor_class)
      url = job_anchor.get_attribute("href")
      assert url
      self.set_url(url)

  # Actually initializes min and max yoe
  def _init_min_yoe(self) -> None:
    self._parse_yoe_from_description()

  def _init_max_yoe(self) -> None:
    pass

  def _init_description(self) -> None:
    description_div_selector = ".JobDetails_jobDescription__uW_fK.JobDetails_blurDescription__vN7nh"
    timeout = 3
    timed_out = True
    start_time = time.time()
    if self.__job_info_div:
      while time.time() - start_time < timeout:
        try:
          description_div = self.__job_info_div.find_element(By.CSS_SELECTOR, description_div_selector)
          timed_out = False
          break
        except NoSuchElementException:
          logging.debug("Waiting for job description div to load...")
          time.sleep(0.1)
      if timed_out:
        raise TimeoutError("Timed out waiting for job description div to load.")
      raw_description = description_div.get_attribute("innerHTML")
      if raw_description is None:
        raw_description = ""
      soup = BeautifulSoup(raw_description, "html.parser")
      description = soup.get_text(separator="\n", strip=True)
      self.set_description(description)
    else:
      self.set_description(None)

  def _init_post_time(self) -> None:
    listing_age_class = "JobCard_listingAge__jJsuc"
    try:
      listing_age = self.__job_listing_li.find_element(By.CLASS_NAME, listing_age_class)
      listing_age_text = listing_age.text
      hours = re.match(r"([0-9]+)h", listing_age_text)
      if hours:
        hours = int(hours.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(hours=hours))
        return
      days = re.match(r"([0-9]+)d", listing_age_text)
      if days:
        days = int(days.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(days=days))
        return
      weeks = re.match(r"([0-9]+)w", listing_age_text)
      if weeks:
        weeks = int(weeks.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=weeks))
        return
      months = re.match(r"([0-9]+)m", listing_age_text)
      if months:
        months = int(months.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=(months * 4.345)))
        return
      years = re.match(r"([0-9]+)y", listing_age_text)
      if years:
        years = int(years.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=(years * 52)))
        return
    except NoSuchElementException:
      pass
    self.set_post_time(None)
