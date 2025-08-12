import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from entities.job_listings.abc_job_listing import JobListing


class IndeedJobListing(JobListing):
  def _init_min_pay(self) -> None:
    pay_h2_selector = ".mosaic-provider-jobcards-4n9q2y.e1tiznh50"
    try:
      pay_h2 = self._get_job_listing_li().find_element(By.CSS_SELECTOR, pay_h2_selector)
      raw_pay = pay_h2.text
      min_salary_from_range_regex = r"\$([0-9]+,?[0-9]+) - \$[0-9]+,?[0-9]+"
      min_salary_from_range_match = re.match(min_salary_from_range_regex, raw_pay)
      if min_salary_from_range_match:
        first_min_salary_from_range_match = str(min_salary_from_range_match.group(1))
        salary_match_as_float = float(first_min_salary_from_range_match.replace(",", ""))
        self.set_min_pay(salary_match_as_float)
        return
      min_hourly_from_range_regex = r"\$([0-9]+) - \$[0-9]+"
      min_hourly_from_range_match = re.match(min_hourly_from_range_regex, raw_pay)
      if min_hourly_from_range_match:
        first_min_hourly_from_range_match = float(min_hourly_from_range_match.group(1)) * 2080
        self.set_min_pay(first_min_hourly_from_range_match)
        return
      single_salary_regex = r"\$([0-9]+,[0-9]+)"
      single_salary_match = re.match(single_salary_regex, raw_pay)
      if single_salary_match:
        first_single_salary_match = str(single_salary_match.group(1))
        salary_match_as_float = float(first_single_salary_match.replace(",", ""))
        self.set_min_pay(salary_match_as_float)
        return
      single_hourly_regex = r"\$([0-9]+)"
      single_hourly_match = re.match(single_hourly_regex, raw_pay)
      if single_hourly_match:
        first_single_hourly_match = float(single_hourly_match.group(1)) * 2080
        self.set_min_pay(first_single_hourly_match)
        return
    except NoSuchElementException:
      pass
    self.set_min_pay(None)

  def _init_max_pay(self) -> None:
    pay_h2_selector = ".mosaic-provider-jobcards-4n9q2y.e1tiznh50"
    try:
      pay_h2 = self._get_job_listing_li().find_element(By.CSS_SELECTOR, pay_h2_selector)
      raw_pay = pay_h2.text
      max_salary_from_range_regex = r"\$[0-9]+,?[0-9]+ - \$([0-9]+,?[0-9]+)"
      max_salary_from_range_match = re.match(max_salary_from_range_regex, raw_pay)
      if max_salary_from_range_match:
        first_max_salary_from_range_match = str(max_salary_from_range_match.group(1))
        salary_match_as_float = float(first_max_salary_from_range_match.replace(",", ""))
        self.set_max_pay(salary_match_as_float)
        return
      max_hourly_from_range_regex = r"\$[0-9]+ - \$([0-9]+)"
      max_hourly_from_range_match = re.match(max_hourly_from_range_regex, raw_pay)
      if max_hourly_from_range_match:
        first_max_hourly_from_range_match = float(max_hourly_from_range_match.group(1)) * 2080
        self.set_max_pay(first_max_hourly_from_range_match)
        return
      single_salary_regex = r"\$([0-9]+,[0-9]+)"
      single_salary_match = re.match(single_salary_regex, raw_pay)
      if single_salary_match:
        first_single_salary_match = str(single_salary_match.group(1))
        salary_match_as_float = float(first_single_salary_match.replace(",", ""))
        self.set_max_pay(salary_match_as_float)
        return
      single_hourly_regex = r"\$([0-9]+)"
      single_hourly_match = re.match(single_hourly_regex, raw_pay)
      if single_hourly_match:
        first_single_hourly_match = float(single_hourly_match.group(1)) * 2080
        self.set_max_pay(first_single_hourly_match)
        return
    except NoSuchElementException:
      pass
    self.set_max_pay(None)

  def _init_title(self) -> None:
    job_listing_h2 = self._get_job_listing_li().find_element(
      By.CSS_SELECTOR,
      "h2.jobTitle"
    )
    self.set_title(job_listing_h2.text.strip())

  def _init_company(self) -> None:
    job_listing_li_spans = self._get_job_listing_li().find_elements(By.TAG_NAME, "span")
    for span in job_listing_li_spans:
      data_test_id = span.get_attribute("data-testid")
      if data_test_id:
        if data_test_id == "company-name":
          self.set_company(span.text.strip())
          return
    raise NoSuchElementException("Failed to find a suitable company element.")

  def _init_location(self) -> None:
    job_listing_li_divs = self._get_job_listing_li().find_elements(By.TAG_NAME, "div")
    for div in job_listing_li_divs:
      data_test_id = div.get_attribute("data-testid")
      if data_test_id:
        if data_test_id == "text-location":
          self.set_location(div.text.strip())
          return
    raise NoSuchElementException("Failed to find a suitable location element.")

  def _init_url(self) -> None:
    title_anchor_selector = ".jcs-JobTitle.css-1baag51.eu4oa1w0"
    title_anchor = self._get_job_listing_li().find_element(By.CSS_SELECTOR, title_anchor_selector)
    url = title_anchor.get_attribute("href")
    assert url
    self.set_url(url)

  # Actually initializes min and max yoe
  def _init_min_yoe(self) -> None:
    self._parse_yoe_from_description()

  def _init_max_yoe(self) -> None:
    pass

  def _init_description(self) -> None:
    job_details_div = self._get_job_details_div()
    if job_details_div:
      job_details_html = job_details_div.get_attribute("innerHTML")
      if job_details_html:
        soup = BeautifulSoup(job_details_html, "html.parser")
        description = soup.get_text(separator="\n", strip=True)
        self.set_description(description)
        return
    self.set_description(None)

  def _init_post_time(self) -> None:
    # Indeed actually doesnt expose this data -- hilarious
    self.set_post_time(None)
