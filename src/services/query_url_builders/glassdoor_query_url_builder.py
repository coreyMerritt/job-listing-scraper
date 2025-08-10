from urllib.parse import quote
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig


class GlassdoorQueryUrlBuilder:
  __easy_apply_only: bool
  __location: str
  __remote: bool
  __min_company_rating: float
  __max_age_in_days: int
  __min_salary: int
  __max_salary: int
  __url: str

  def __init__(self, universal_config: UniversalConfig, quick_settings: QuickSettings):
    self.__easy_apply_only = quick_settings.bot_behavior.easy_apply_only.glassdoor
    if universal_config.search.location.city:
      self.__location = universal_config.search.location.city
    else:
      self.__location = "United%20States"   # TODO: We need to figure out some better way to handle null
    self.__remote = universal_config.search.location.remote
    if universal_config.search.misc.min_company_rating:
      self.__min_company_rating = universal_config.search.misc.min_company_rating
    else:
      self.__min_company_rating = 0
    self.__max_age_in_days = universal_config.search.misc.max_age_in_days
    if universal_config.search.salary.min:
      self.__min_salary = universal_config.search.salary.min
    else:
      self.__min_salary = 0           # TODO: We need to figure out some better way to handle null
    if universal_config.search.salary.max:
      self.__max_salary = universal_config.search.salary.max
    else:
      self.__max_salary = 1000000      # TODO: We need to figure out some better way to handle null
    self.__url = ""

  def build(self, search_term: str) -> str:
    self.__add_base()
    self.__add_location()
    self.__add_search_term(search_term)
    self.__add_remote()
    self.__add_min_company_rating()
    self.__add_max_age()
    self.__add_min_salary()
    self.__add_max_salary()
    self.__add_easy_apply_only()
    return self.__url

  def __add_base(self) -> None:
    self.__url = "https://www.glassdoor.com/Job/"

  def __add_location(self) -> None:
    location = quote(self.__location)
    self.__url += location

  def __add_search_term(self, term: str) -> None:
    location_length_plus_one = len(self.__location) + 1
    location_length_plus_one_plus_term_length = location_length_plus_one + len(term)
    self.__url += f"-{term}-jobs-SRCH_IL.0,13_IN1_KO{location_length_plus_one},{location_length_plus_one_plus_term_length}.htm?"    # pylint: disable=line-too-long

  def __add_remote(self) -> None:
    if self.__remote:
      remote_as_num = 1
    else:
      remote_as_num = 0
    self.__url += f"remoteWorkType={remote_as_num}"

  def __add_min_company_rating(self) -> None:
    self.__url += f"&minRating={self.__min_company_rating}"

  def __add_max_age(self) -> None:
    self.__url += f"&fromAge={self.__max_age_in_days}"

  def __add_min_salary(self) -> None:
    self.__url += f"&minSalary={self.__min_salary}"

  def __add_max_salary(self) -> None:
    self.__url += f"&maxSalary={self.__max_salary}"

  def __add_easy_apply_only(self) -> None:
    if self.__easy_apply_only:
      self.__url += "&applicationType=1"
