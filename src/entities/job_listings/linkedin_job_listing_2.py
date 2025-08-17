import logging
import time
import re
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from entities.job_listings.abc_job_listing import JobListing
from services.misc.language_parser import LanguageParser


class LinkedinJobListing2(JobListing):
  __job_header_div: WebElement | None

  def __init__(
    self,
    language_parser: LanguageParser,
    job_listing_li: WebElement,
    job_details_div: WebElement | None = None,
    job_header_div: WebElement | None = None
  ):
    self.__job_header_div = job_header_div
    super().__init__(language_parser, job_listing_li, job_details_div)

  # Actually initializes min and max pay -- its not super easy to seperate them without redundant calulcations
  def _init_min_pay(self) -> None:
    try:
      relative_pay_div_xpath = "./div/a/div/div/div[2]/div[1]/div[4]/div[1]"
      pay_div = self._get_job_listing_li().find_element(By.XPATH, relative_pay_div_xpath)
      self.__handle_linkedin_pay(pay_div.text)
    except NoSuchElementException:
      self.set_min_pay(None)
      self.set_max_pay(None)

  def _init_max_pay(self) -> None:
    pass

  def _init_title(self) -> None:
    title_anchor_selector = ".disabled.ember-view.job-card-container__link.OzlfXcDyufshDyxcxHnzuayNiPLsbOSuFdfcs.job-card-list__title--link"    # pylint: disable=line-too-long
    title_anchor = self._get_job_listing_li().find_element(By.CSS_SELECTOR, title_anchor_selector)
    raw_title = title_anchor.get_attribute("aria-label")
    if raw_title:
      title = raw_title.strip()
      self.set_title(title)
      return
    raise NoSuchElementException("Failed to find a proper title anchor.")

  def _init_company(self) -> None:
    company_span_class = "nZRzizuJPSzSZDGSlDorCIpYNKxkEYXVs"
    company_span = self._get_job_listing_li().find_element(By.CLASS_NAME, company_span_class)
    self.set_company(company_span.text.strip())

  def _init_location(self) -> None:
    relative_location_li_xpath = "./div/div/div[1]/div/div[2]/div[3]/ul/li/span"
    location_span = self._get_job_listing_li().find_element(By.XPATH, relative_location_li_xpath)
    self.set_location(location_span.text)

  def _init_url(self) -> None:
    title_anchor_selector = ".disabled.ember-view.job-card-container__link.OzlfXcDyufshDyxcxHnzuayNiPLsbOSuFdfcs.job-card-list__title--link"    # pylint: disable=line-too-long
    url_anchor = self._get_job_listing_li().find_element(By.CSS_SELECTOR, title_anchor_selector)
    href = url_anchor.get_attribute("href")
    assert href
    job_id_regex = r"\/jobs\/view\/([0-9]+)"
    match = re.search(job_id_regex, href)
    assert match
    job_id = match.group(1)
    url = f"https://www.linkedin.com/jobs/view/{job_id}"
    self.set_url(url)

  # Actually initializes min and max yoe
  def _init_min_yoe(self) -> None:
    self._parse_yoe_from_description()

  def _init_max_yoe(self) -> None:
    pass

  def _init_description(self) -> None:
    job_details_div = self._get_job_details_div()
    if job_details_div:
      self.__wait_for_populated_description(job_details_div)
      raw_description = job_details_div.get_attribute("outerHTML") or ""
      soup = BeautifulSoup(raw_description, "html.parser")
      description = soup.get_text(separator="\n", strip=True)
      self.set_description(description)
    else:
      self.set_description(None)

  def _init_post_time(self) -> None:
    if self.__job_header_div:
      job_details_html = self.__job_header_div.get_attribute("innerHTML")
      assert job_details_html
      full_text_match_regex = r"([0-9]+) (.+) ago"
      full_text_match = re.search(full_text_match_regex, job_details_html)
      if not full_text_match:
        logging.warning("No post time available...")
        # This is very rare, so this ensures that if we're triggering an unknown
        # error repeatedly, we'll notice because the system will slow dramatically
        time.sleep(3)
        self.set_post_time(None)
        return
      amount, unit = full_text_match.groups()
      if "minute" in unit:
        minutes = float(amount)
        self.set_post_time(datetime.now(timezone.utc) - timedelta(minutes=minutes))
        return
      elif "hour" in unit:
        hours = float(amount)
        self.set_post_time(datetime.now(timezone.utc) - timedelta(hours=hours))
        return
      elif "day" in unit:
        days = float(amount)
        self.set_post_time(datetime.now(timezone.utc) - timedelta(days=days))
        return
      elif "week" in unit:
        weeks = float(amount)
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=weeks))
        return
      elif "month" in unit:
        months = float(amount)
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=(months * 4.345)))
        return
      elif "year" in unit:
        years = float(amount)
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=(years * 52)))
        return
    try:
      listing_age = self._get_job_listing_li().find_element(By.TAG_NAME, "time")
      listing_age_text = listing_age.text
      minutes = re.search(r"([0-9]+) minute[s]? ago", listing_age_text)
      if minutes:
        minutes = int(minutes.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(minutes=minutes))
        return
      hours = re.search(r"([0-9]+) hour[s]? ago", listing_age_text)
      if hours:
        hours = int(hours.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(hours=hours))
        return
      days = re.search(r"([0-9]+) day[s]? ago", listing_age_text)
      if days:
        days = int(days.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(days=days))
        return
      weeks = re.search(r"([0-9]+) week[s]? ago", listing_age_text)
      if weeks:
        weeks = int(weeks.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=weeks))
        return
      months = re.search(r"([0-9]+) month[s]? ago", listing_age_text)
      if months:
        months = int(months.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=(months * 4.345)))
        return
      years = re.search(r"([0-9]+) year[s]? ago", listing_age_text)
      if years:
        years = int(years.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=(years * 52)))
        return
    except NoSuchElementException:
      pass
    self.set_post_time(None)

  def __wait_for_populated_description(self, element: WebElement, timeout=5.0) -> None:
    start = time.time()
    while time.time() - start < timeout:
      text = element.text.strip()
      IS_LOADED = len(text.splitlines()) > 2 or len(text) > 100
      if IS_LOADED:
        return
      time.sleep(0.1)

  def __handle_linkedin_pay(self, raw_pay_string: str) -> None:
    raw_pay_string = raw_pay_string.lower().strip()
    IS_GARBAGE = "/hr" not in raw_pay_string and "/yr" not in raw_pay_string
    if IS_GARBAGE:
      self.set_min_pay(None)
      self.set_max_pay(None)
      return
    IS_RANGE = "-" in raw_pay_string
    IS_ANNUAL = "/yr" in raw_pay_string
    IS_HOURLY = "/hr" in raw_pay_string
    HOURLY_TO_SALARY_CONST = 2080
    K_TO_TRUE_SALARY_CONST = 1000
    if IS_RANGE:
      values = re.findall(r"\$[0-9]+(?:\.[0-9]{1,2})?", raw_pay_string)
      if IS_HOURLY:
        hourly_values = [float(v.replace("$", "")) * HOURLY_TO_SALARY_CONST for v in values if v.strip()]
        if len(hourly_values) == 2:
          self.set_min_pay(hourly_values[0])
          self.set_max_pay(hourly_values[1])
          return
      elif IS_ANNUAL:
        salary_values = [float(v.replace("$", "")) * K_TO_TRUE_SALARY_CONST for v in values if v.strip()]
        if len(salary_values) == 2:
          self.set_min_pay(salary_values[0])
          self.set_max_pay(salary_values[1])
          return
    else:
      match = re.search(r"\$[0-9]+(?:\.[0-9]{1,2})?", raw_pay_string)
      if match:
        value = float(match.group().replace("$", ""))
        if IS_HOURLY:
          value *= HOURLY_TO_SALARY_CONST
        elif IS_ANNUAL:
          value *= K_TO_TRUE_SALARY_CONST
        if "up to" in raw_pay_string:
          self.set_min_pay(None)
        else:
          self.set_min_pay(value)
        self.set_max_pay(value)
        return
    self.set_min_pay(None)
    self.set_max_pay(None)
