from typing import List

from models.configs.universal_config import UniversalConfig


class IndeedQueryUrlBuilder:
  __ignore_terms: List[str]
  __location: str | None
  __max_age_in_days: int
  __min_salary: int
  __max_distance_in_mis: int
  __remote: bool
  __hybrid: bool
  __entry_level: bool
  __mid_level: bool
  __senior_level: bool
  __url: str

  def __init__(self, universal_config: UniversalConfig):
    self.__ignore_terms = universal_config.search.terms.ignore
    self.__location = universal_config.search.location.city
    self.__max_age_in_days = universal_config.search.misc.max_age_in_days
    if universal_config.search.salary.min:
      self.__min_salary = universal_config.search.salary.min
    else:
      self.__min_salary = 0       # TODO: We need to figure out some better way to handle null
    self.__max_distance_in_mis = universal_config.search.location.max_distance_in_mis
    self.__remote = universal_config.search.location.remote
    self.__hybrid = universal_config.search.location.hybrid
    self.__entry_level = universal_config.search.experience.entry
    self.__mid_level = universal_config.search.experience.mid
    self.__senior_level = universal_config.search.experience.senior
    self.__url = ""

  def build(self, term: str) -> str:
    self.__add_base()
    self.__add_search_term(term)
    self.__add_ignore_terms()
    self.__add_always_params()
    self.__add_location()
    self.__add_max_age()
    self.__add_min_salary()
    self.__add_max_distance()
    self.__add_pre_attributes_tag_if_needed()
    self.__add_remote_if_needed()
    self.__add_hybrid_if_needed()
    # self.__add_exp_level_tags_as_needed()
    self.__add_post_attributes_tag_if_needed()
    return self.__url

  def __add_base(self) -> None:
    self.__url = "https://www.indeed.com/jobs?"

  def __add_search_term(self, term: str) -> None:
    self.__url += f"q=%28{term}%29"

  def __add_ignore_terms(self) -> None:
    for term in self.__ignore_terms:
      self.__url += f"+-{term}"

  def __add_always_params(self) -> None:
    self.__url += "&from=searchOnDesktopSerp"

  def __add_location(self) -> None:
    if self.__remote:
      self.__url += '&l="remote"'
    elif self.__location:
      self.__url += f"&l={self.__location}"
    else:
      self.__url += "&l="

  def __add_max_age(self) -> None:
    self.__url += f"&fromage={self.__max_age_in_days}"

  def __add_min_salary(self) -> None:
    self.__url += f"&salaryType=%24{self.__min_salary}%2B"

  def __add_max_distance(self) -> None:
    self.__url += f"&radius={self.__max_distance_in_mis}"

  def __add_pre_attributes_tag_if_needed(self) -> None:
    pre_tag_needed = False
    if self.__entry_level or self.__mid_level or self.__senior_level:
      pre_tag_needed = True
    if self.__entry_level and self.__mid_level and self.__senior_level:
      pre_tag_needed = False
    if self.__remote or self.__hybrid:
      pre_tag_needed = True
    if pre_tag_needed:
      self.__url += "&sc=0kf%3A"

  def __add_remote_if_needed(self) -> None:
    assert "&sc=0kf%3A" in self.__url
    if self.__remote:
      self.__url += "attr%28DSQF7%29"

  def __add_hybrid_if_needed(self) -> None:
    if not self.__remote:
      assert "&sc=0kf%3A" in self.__url
      if self.__hybrid:
        self.__url += "attr%28PAXZC%29"

  def __add_post_attributes_tag_if_needed(self) -> None:
    post_tag_needed = False
    if self.__entry_level or self.__mid_level or self.__senior_level:
      post_tag_needed = True
    if self.__entry_level and self.__mid_level and self.__senior_level:
      post_tag_needed = False
    if self.__remote or self.__hybrid:
      post_tag_needed = True
    if post_tag_needed:
      self.__url += "%3B"
