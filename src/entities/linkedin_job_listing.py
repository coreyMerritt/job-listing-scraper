import time
import re
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from entities.abc_job_listing import JobListing
from services.misc.language_parser import LanguageParser


class LinkedinJobListing(JobListing):
  __job_listing_li: WebElement
  __url: str | None
  __job_description_content_div: WebElement | None

  def __init__(
    self,
    language_parser: LanguageParser,
    job_listing_li: WebElement,
    job_description_content_div: WebElement | None = None,
    url: str | None = None
  ):
    self.__job_listing_li = job_listing_li
    self.__url = url
    self.__job_description_content_div = job_description_content_div
    super().__init__(language_parser)

  # Actually initializes min and max pay -- its not super easy to seperate them without redundant calulcations
  def _init_min_pay(self) -> None:
    try:
      relative_pay_div_xpath = "./div/a/div/div/div[2]/div[1]/div[4]/div[1]"
      pay_div = self.__job_listing_li.find_element(By.XPATH, relative_pay_div_xpath)
      self.__handle_linkedin_pay(pay_div.text)
    except NoSuchElementException:
      self.set_min_pay(None)
      self.set_max_pay(None)

  def _init_max_pay(self) -> None:
    pass

  def _init_title(self) -> None:
    relative_job_title_span_xpath = "./div/a/div/div/div[2]/div[1]/div[1]/span[1]/strong"
    job_title_span = self.__job_listing_li.find_element(By.XPATH, relative_job_title_span_xpath)
    self.set_title(job_title_span.text)

  def _init_company(self) -> None:
    relative_company_div_xpath = "./div/a/div/div/div[2]/div[1]/div[2]/div"
    company_div = self.__job_listing_li.find_element(By.XPATH, relative_company_div_xpath)
    self.set_company(company_div.text)

  def _init_location(self) -> None:
    relative_location_div_xpath = "./div/a/div/div/div[2]/div[1]/div[3]/div"
    location_div = self.__job_listing_li.find_element(By.XPATH, relative_location_div_xpath)
    self.set_location(location_div.text)

  def _init_url(self) -> None:
    if self.__url:
      self.set_url(self.__url)
    else:
      job_listing_anchor = self.__job_listing_li.find_element(By.XPATH, "./div/a")
      url = job_listing_anchor.get_attribute("href")
      assert url
      self.set_url(url)

  # Actually initializes min and max yoe
  def _init_min_yoe(self) -> None:
    self._parse_yoe_from_description()

  def _init_max_yoe(self) -> None:
    pass

  def _init_description(self) -> None:
    if self.__job_description_content_div:
      self.__wait_for_populated_description(self.__job_description_content_div)
      raw_description = self.__job_description_content_div.get_attribute("outerHTML") or ""
      soup = BeautifulSoup(raw_description, "html.parser")
      description = soup.get_text(separator="\n", strip=True)
      self.set_description(description)
    else:
      self.set_description(None)

  def _init_post_time(self) -> None:
    try:
      listing_age = self.__job_listing_li.find_element(By.TAG_NAME, "time")
      listing_age_text = listing_age.text
      hours = re.match(r"([0-9]+) hour[s]? ago", listing_age_text)
      if hours:
        hours = int(hours.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(hours=hours))
        return
      days = re.match(r"([0-9]+) day[s]? ago", listing_age_text)
      if days:
        days = int(days.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(days=days))
        return
      weeks = re.match(r"([0-9]+) week[s]? ago", listing_age_text)
      if weeks:
        weeks = int(weeks.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=weeks))
        return
      months = re.match(r"([0-9]+) month[s]? ago", listing_age_text)
      if months:
        months = int(months.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=(months * 4.345)))
        return
      years = re.match(r"([0-9]+) year[s]? ago", listing_age_text)
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
      elif IS_ANNUAL:
        salary_values = [float(v.replace("$", "")) * K_TO_TRUE_SALARY_CONST for v in values if v.strip()]
        if len(salary_values) == 2:
          self.set_min_pay(salary_values[0])
          self.set_max_pay(salary_values[1])
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
