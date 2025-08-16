import logging
import re
import time
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from entities.job_listings.abc_job_listing import JobListing


class GlassdoorJobListing(JobListing):
  def _init_min_pay(self) -> None:
    try:
      job_salary_div_class = "JobCard_salaryEstimate__QpbTW"
      job_salary_div = self._get_job_listing_li().find_element(By.CLASS_NAME, job_salary_div_class)
      job_salary_div_text = job_salary_div.text
      min_salary_from_range_regex = r"\$([0-9]+)[k|K] - \$[0-9]+[k|K]"
      min_salary_from_range_match = re.search(min_salary_from_range_regex, job_salary_div_text)
      if min_salary_from_range_match:
        first_min_salary_from_range_match = float(min_salary_from_range_match.group(1)) * 1000
        self.set_min_pay(first_min_salary_from_range_match)
        return
      min_hourly_from_range_regex = r"\$([0-9]+[.]?[0-9]+) - \$[0-9]+[.]?[0-9]+"
      min_hourly_from_range_match = re.search(min_hourly_from_range_regex, job_salary_div_text)
      if min_hourly_from_range_match:
        first_min_hourly_from_range_match = float(min_hourly_from_range_match.group(1)) * 2080
        self.set_min_pay(first_min_hourly_from_range_match)
        return
      single_hourly_regex = r"\$([0-9]+[.]?[0-9]+)"
      single_hourly_match = re.search(single_hourly_regex, job_salary_div_text)
      if single_hourly_match:
        first_single_hourly_match = float(single_hourly_match.group(1)) * 2080
        self.set_min_pay(first_single_hourly_match)
        return
      single_salary_regex = r"\$([0-9]+)[k|K]"
      single_salary_match = re.search(single_salary_regex, job_salary_div_text)
      if single_salary_match:
        first_single_salary_match = float(single_salary_match.group(1)) * 1000
        self.set_min_pay(first_single_salary_match)
        return
    except NoSuchElementException:
      pass
    self.set_min_pay(None)

  def _init_max_pay(self) -> None:
    try:
      job_salary_div_class = "JobCard_salaryEstimate__QpbTW"
      job_salary_div = self._get_job_listing_li().find_element(By.CLASS_NAME, job_salary_div_class)
      job_salary_div_text = job_salary_div.text
      max_salary_from_range_regex = r"\$[0-9]+[k|K] - \$([0-9]+)[k|K]"
      max_salary_from_range_match = re.search(max_salary_from_range_regex, job_salary_div_text)
      if max_salary_from_range_match:
        first_max_salary_from_range_match = float(max_salary_from_range_match.group(1)) * 1000
        self.set_max_pay(first_max_salary_from_range_match)
        return
      max_hourly_from_range_regex = r"\$[0-9]+[.]?[0-9]+ - \$([0-9]+[.]?[0-9]+)"
      max_hourly_from_range_match = re.search(max_hourly_from_range_regex, job_salary_div_text)
      if max_hourly_from_range_match:
        first_max_hourly_from_range_match = float(max_hourly_from_range_match.group(1)) * 2080
        self.set_max_pay(first_max_hourly_from_range_match)
        return
      single_salary_regex = r"\$([0-9]+)[k|K]"
      single_salary_match = re.search(single_salary_regex, job_salary_div_text)
      if single_salary_match:
        first_single_salary_match = float(single_salary_match.group(1)) * 1000
        self.set_max_pay(first_single_salary_match)
        return
      single_hourly_regex = r"\$([0-9]+[.]?[0-9]+)"
      single_hourly_match = re.search(single_hourly_regex, job_salary_div_text)
      if single_hourly_match:
        first_single_hourly_match = float(single_hourly_match.group(1)) * 2080
        self.set_max_pay(first_single_hourly_match)
        return
    except NoSuchElementException:
      pass
    self.set_max_pay(None)

  def _init_title(self) -> None:
    job_title_anchor_class = "JobCard_jobTitle__GLyJ1"
    job_title_anchor = self._get_job_listing_li().find_element(By.CLASS_NAME, job_title_anchor_class)
    self.set_title(job_title_anchor.text.strip())

  def _init_company(self) -> None:
    company_span_class = "EmployerProfile_compactEmployerName__9MGcV"
    company_span = self._get_job_listing_li().find_element(By.CLASS_NAME, company_span_class)
    self.set_company(company_span.text.strip())

  def _init_location(self) -> None:
    location_div_class = "JobCard_location__Ds1fM"
    location_div = self._get_job_listing_li().find_element(By.CLASS_NAME, location_div_class)
    self.set_location(location_div.text.strip())

  def _init_url(self) -> None:
    title_anchor_class = "JobCard_jobTitle__GLyJ1"
    title_anchor = self._get_job_listing_li().find_element(By.CLASS_NAME, title_anchor_class)
    job_url = title_anchor.get_attribute("href")
    assert job_url
    self.set_url(job_url)

  # Actually initializes min and max yoe
  def _init_min_yoe(self) -> None:
    self._parse_yoe_from_description()

  def _init_max_yoe(self) -> None:
    pass

  def _init_description(self) -> None:
    description_div_selectors = [
      ".JobDetails_jobDescription__uW_fK.JobDetails_blurDescription__vN7nh",
      ".JobDetails_jobDescription__uW_fK.JobDetails_showHidden__C_FOA"
    ]
    timeout = 3.0
    timed_out = True
    start_time = time.time()
    job_details_div = self._get_job_details_div()
    if job_details_div:
      while time.time() - start_time < timeout:
        for selector in description_div_selectors:
          try:
            description_div = job_details_div.find_element(By.CSS_SELECTOR, selector)
            timed_out = False
            break
          except NoSuchElementException:
            logging.debug("Waiting for job description div to load...")
            time.sleep(0.1)
        if description_div:
          break
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
      listing_age = self._get_job_listing_li().find_element(By.CLASS_NAME, listing_age_class)
      listing_age_text = listing_age.text
      hours = re.search(r"([0-9]+)h", listing_age_text)
      if hours:
        hours = int(hours.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(hours=hours))
        return
      days = re.search(r"([0-9]+)d", listing_age_text)
      if days:
        days = int(days.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(days=days))
        return
      weeks = re.search(r"([0-9]+)w", listing_age_text)
      if weeks:
        weeks = int(weeks.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=weeks))
        return
      months = re.search(r"([0-9]+)m", listing_age_text)
      if months:
        months = int(months.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=(months * 4.345)))
        return
      years = re.search(r"([0-9]+)y", listing_age_text)
      if years:
        years = int(years.group(1))
        self.set_post_time(datetime.now(timezone.utc) - timedelta(weeks=(years * 52)))
        return
    except NoSuchElementException:
      pass
    self.set_post_time(None)
