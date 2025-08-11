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

  def __init__(self, universal_config: UniversalConfig, quick_settings: QuickSettings):   # pylint: disable=unused-argument
    self.__easy_apply_only = False
    if universal_config.search.location.city:
      self.__location = quote(universal_config.search.location.city.lower().replace(" ", "-"))
    else:
      # TODO: We need to figure out some better way to handle null
      self.__location = quote("United States".lower().replace(" ", "-"))
    self.__remote = universal_config.search.location.remote
    if universal_config.search.misc.min_company_rating:
      self.__min_company_rating = universal_config.search.misc.min_company_rating
    else:
      self.__min_company_rating = 0
    self.__max_age_in_days = universal_config.search.misc.max_age_in_days
    if universal_config.search.salary.min:
      self.__min_salary = universal_config.search.salary.min
    else:
      # TODO: We need to figure out some better way to handle null
      self.__min_salary = 0
    if universal_config.search.salary.max:
      self.__max_salary = universal_config.search.salary.max
    else:
      # TODO: We need to figure out some better way to handle null
      self.__max_salary = 1000000
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
    self.__url += self.__location

  def __add_search_term(self, term: str) -> None:
    encoded_location = self.__location
    encoded_term = quote(term)
    location_start = 0
    location_end = len(encoded_location)
    term_start = location_end + 1
    term_end = term_start + len(encoded_term)
    self.__url += (
      f"-{encoded_term}-jobs-SRCH_IL.{location_start},{location_end}"
      f"_IN1_KO{term_start},{term_end}.htm?"
    )

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
