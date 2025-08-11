from typing import List
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import UniversalConfig


class LinkedinQueryUrlBuilder:
  __ignore_terms: List[str]
  __location: str | None
  __max_age_in_days: int
  __remote: bool
  __hybrid: bool
  __entry_level: bool
  __mid_level: bool
  __senior_level: bool
  __easy_apply_only: bool
  __url: str

  def __init__(
    self,
    universal_config: UniversalConfig,
    quick_settings: QuickSettings
  ):
    self.__ignore_terms = universal_config.search.terms.ignore
    self.__location = universal_config.search.location.city
    self.__max_age_in_days = universal_config.search.misc.max_age_in_days
    self.__remote = universal_config.search.location.remote
    self.__hybrid = universal_config.search.location.hybrid
    self.__entry_level = universal_config.search.experience.entry
    self.__mid_level = universal_config.search.experience.mid
    self.__senior_level = universal_config.search.experience.senior
    self.__easy_apply_only = False
    self.__url = ""

  def build(self, search_term: str) -> str:
    self.__add_base()
    self.__add_location()
    self.__add_remote_hybrid_onsite()
    self.__add_experience_level()
    self.__add_max_age()
    self.__add_easy_apply_only()
    self.__add_search_term(search_term)
    return self.__url

  def __add_base(self) -> None:
    self.__url = "https://www.linkedin.com/jobs/search-results/?"

  def __add_location(self) -> None:
    if self.__location:
      self.__url += f"&location={self.__location}"

  def __add_remote_hybrid_onsite(self) -> None:
    if self.__remote:
      self.__url += "&f_WT=2"
    elif self.__hybrid:
      self.__url += "&f_WT=3"
    else:
      self.__url += "&f_WT=1"

  def __add_experience_level(self) -> None:
    if not self.__entry_level and not self.__mid_level and not self.__senior_level:
      return
    self.__url += "&f_E="
    if self.__entry_level:
      for i in range(1, 4):
        if self.__url[-1] == "=":
          self.__url += str(i)
        elif int(self.__url[-1]) >= i:
          pass
        else:
          self.__url += f",{i}"
    if self.__mid_level:
      for i in range(3, 5):
        if self.__url[-1] == "=":
          self.__url += str(i)
        elif int(self.__url[-1]) >= i:
          pass
        else:
          self.__url += f",{i}"
    if self.__senior_level:
      for i in range(4, 7):
        if self.__url[-1] == "=":
          self.__url += str(i)
        elif int(self.__url[-1]) >= i:
          pass
        else:
          self.__url += f",{i}"

  def __add_max_age(self) -> None:
    self.__url += f"&f_TPR=r{self.__max_age_in_days * 86400}"

  def __add_easy_apply_only(self) -> None:
    self.__url += "&f_AL="
    if self.__easy_apply_only:
      self.__url += "true"
    else:
      self.__url += "false"

  def __add_search_term(self, search_term: str) -> None:
    self.__url += "&keywords="
    if self.__remote:
      self.__url += "remote%20"
    self.__url += search_term
    self.__add_ignore_terms()

  def __add_ignore_terms(self) -> None:
    if len(self.__ignore_terms) > 0:
      self.__url += "%20NOT%20%28"
      first_ignore_term = self.__ignore_terms[0]
      self.__url += first_ignore_term
      for term in self.__ignore_terms:
        if term != first_ignore_term:
          self.__url += f"%20or%20{term}"
      self.__url += "%29"
