from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from bs4 import BeautifulSoup
from entities.abc_job_listing import JobListing
from services.misc.language_parser import LanguageParser


class IndeedJobListing(JobListing):
  __job_description_html: str | None
  __url: str | None
  __job_listing_li: WebElement

  def __init__(
    self,
    language_parser: LanguageParser,
    job_listing_li: WebElement,
    job_description_html: str | None = None,
    url: str | None = None
  ):
    self.__job_description_html = job_description_html
    self.__url = url
    self.__job_listing_li = job_listing_li
    super().__init__(language_parser)

  # TODO: Implement
  def _init_min_pay(self) -> None:
    self.set_min_pay(None)

  # TODO: Implement
  def _init_max_pay(self) -> None:
    self.set_max_pay(None)

  def _init_title(self) -> None:
    relative_title_span_xpath = "./div/div/div/div/div/div/table/tbody/tr/td/div[1]/h2/a/span"
    relative_title_span = self.__job_listing_li.find_element(By.XPATH, relative_title_span_xpath)
    self.set_title(relative_title_span.text.strip())

  def _init_company(self) -> None:
    relative_company_span_xpath = "./div/div/div/div/div/div/table/tbody/tr/td/div[2]/div/div[1]/span"
    relative_company_span = self.__job_listing_li.find_element(By.XPATH, relative_company_span_xpath)
    self.set_company(relative_company_span.text.strip())

  def _init_location(self) -> None:
    relative_location_div_xpath = "./div/div/div/div/div/div/table/tbody/tr/td/div[2]/div/div[2]"
    relative_location_div = self.__job_listing_li.find_element(By.XPATH, relative_location_div_xpath)
    self.set_location(relative_location_div.text.strip())

  def _init_url(self) -> None:
    if self.__url:
      self.set_url(self.__url)
    else:
      relative_title_anchor_xpath = "./div/div/div/div/div/div/table/tbody/tr/td/div[1]/h2/a"
      relative_title_anchor = self.__job_listing_li.find_element(By.XPATH, relative_title_anchor_xpath)
      url = relative_title_anchor.get_attribute("href")
      assert url
      self.set_url(url)

  # Actually initializes min and max yoe
  def _init_min_yoe(self) -> None:
    self._parse_yoe_from_description()

  def _init_max_yoe(self) -> None:
    pass

  def _init_description(self) -> None:
    if self.__job_description_html:
      soup = BeautifulSoup(self.__job_description_html, "html.parser")
      description = soup.get_text(separator="\n", strip=True)
      self.set_description(description)
    else:
      self.set_description(None)

  def _init_post_time(self) -> None:
    # Indeed actually doesnt expose this data -- hilarious
    self.set_post_time(None)
