from abc import ABC, abstractmethod
from datetime import datetime
import json
import logging
from selenium.webdriver.remote.webelement import WebElement
from models.enums.language import Language
from services.misc.language_parser import LanguageParser
from services.misc.yoe_parser import YoeParser


class JobListing(ABC):
  __job_listing_li: WebElement
  __job_details_div: WebElement | None
  __title: str
  __company: str
  __location: str
  __url: str
  __language: Language
  __min_yoe: int | None
  __max_yoe: int | None
  __min_pay: float | None
  __max_pay: float | None
  __description: str | None
  __post_time: datetime | None

  def __init__(
    self,
    language_parser: LanguageParser,
    job_listing_li: WebElement,
    job_details_div: WebElement | None = None
  ):
    self.__job_listing_li = job_listing_li
    self.__job_details_div = job_details_div
    self._init_title()
    self._init_company()
    self._init_location()
    self._init_min_pay()
    self._init_max_pay()
    self._init_url()
    self._init_language(language_parser)
    self._init_description()
    self._init_min_yoe()
    self._init_max_yoe()
    self._init_post_time()

  @abstractmethod
  def _init_min_pay(self) -> None:
    pass

  @abstractmethod
  def _init_max_pay(self) -> None:
    pass

  @abstractmethod
  def _init_title(self) -> None:
    pass

  @abstractmethod
  def _init_company(self) -> None:
    pass

  @abstractmethod
  def _init_location(self) -> None:
    pass

  @abstractmethod
  def _init_url(self) -> None:
    pass

  def _init_language(self, language_parser: LanguageParser) -> None:
    content_blob = ""
    content_blob += f"{self.get_title()} "
    content_blob += f"{self.get_company()} "
    content_blob += self.get_location()
    self.__language = language_parser.get_language(content_blob)

  @abstractmethod
  def _init_min_yoe(self) -> None:
    pass

  @abstractmethod
  def _init_max_yoe(self) -> None:
    pass

  @abstractmethod
  def _init_description(self) -> None:
    pass

  @abstractmethod
  def _init_post_time(self) -> None:
    pass

  def get_min_pay(self) -> float | None:
    return self.__min_pay

  def get_max_pay(self) -> float | None:
    return self.__max_pay

  def get_title(self) -> str:
    return self.__title

  def get_company(self) -> str:
    return self.__company

  def get_location(self) -> str:
    return self.__location

  def get_url(self) -> str:
    return self.__url

  def get_language(self) -> Language:
    return self.__language

  def get_min_yoe(self) -> int | None:
    return self.__min_yoe

  def get_max_yoe(self) -> int | None:
    return self.__max_yoe

  def get_description(self) -> str | None:
    return self.__description

  def get_post_time(self) -> datetime | None:
    return self.__post_time

  def _get_job_listing_li(self) -> WebElement:
    return self.__job_listing_li

  def _get_job_details_div(self) -> WebElement | None:
    return self.__job_details_div

  def set_min_pay(self, pay: float | None) -> None:
    self.__min_pay = pay

  def set_max_pay(self, pay: float | None) -> None:
    self.__max_pay = pay

  def set_title(self, title: str) -> None:
    self.__title = title

  def set_company(self, company: str) -> None:
    self.__company = company

  def set_location(self, location: str) -> None:
    self.__location = location

  def set_url(self, url: str) -> None:
    self.__url = url

  def set_language(self, language: Language) -> None:
    self.__language = language

  def set_min_yoe(self, yoe: int | None) -> None:
    self.__min_yoe = yoe

  def set_max_yoe(self, yoe: int | None) -> None:
    self.__max_yoe = yoe

  def set_description(self, description: str | None) -> None:
    self.__description = description

  def set_post_time(self, post_time: datetime | None) -> None:
    self.__post_time = post_time

  def print_all(self) -> None:
    if self.get_description():
      description_indentation="\n\n"
    else:
      description_indentation="\t"
    logging.info(
      "\nTitle:\t\t%s\nCompany:\t%s\nLocation:\t%s\nMin Pay:\t%s\nMax Pay:\t%s\nDescription:%s%s\n",
      self.get_title(),
      self.get_company(),
      self.get_location(),
      self.get_min_pay(),
      self.get_max_pay(),
      description_indentation,
      self.get_description()
    )

  def print_most(self) -> None:
    logging.info(
      "\n\nPost Time:\t%s\nLanguage:\t%s\n\nTitle:\t\t%s\nCompany:\t%s\nLocation:\t%s\nMin Pay:\t%s\nMax Pay:\t%s\nMin YoE:\t%s\nMax YoE:\t%s\n",   # pylint: disable=line-too-long
      self.get_post_time(),
      self.get_language().value,
      self.get_title(),
      self.get_company(),
      self.get_location(),
      self.get_min_pay(),
      self.get_max_pay(),
      self.get_min_yoe(),
      self.get_max_yoe(),
    )

  def to_minimal_dict(self) -> dict[str, str | float | None]:
    return {
      "title": self.get_title(),
      "company": self.get_company(),
      "location": self.get_location()
    }

  def to_dict(self) -> dict[str, str | float | None]:
    return {
      "title": self.get_title(),
      "company": self.get_company(),
      "location": self.get_location(),
      "min_pay": self.get_min_pay(),
      "max_pay": self.get_max_pay(),
      "min_yoe": self.get_min_yoe(),
      "max_yoe": self.get_max_yoe(),
      "description": self.get_description()
    }

  def to_minimal_str(self) -> str:
    return json.dumps(self.to_minimal_dict(), sort_keys=True)

  def _parse_yoe_from_description(self) -> None:
    description = self.get_description()
    if description:
      yoe_parser = YoeParser()
      min_yoe, max_yoe = yoe_parser.parse(description)
      self.set_min_yoe(min_yoe)
      self.set_max_yoe(max_yoe)
    else:
      self.set_min_yoe(None)
      self.set_max_yoe(None)
