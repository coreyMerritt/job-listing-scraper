import logging
import re
from typing import List
from entities.job_listings.abc_job_listing import JobListing
from models.configs.quick_settings import QuickSettings
from models.configs.universal_config import SearchSalary, UniversalConfig, YearsOfExperience
from models.enums.language import Language
from models.enums.ignore_category import IgnoreCategory
from models.enums.ignore_type import IgnoreType


class JobApplication():
  __applied: bool
  __first_name: str
  __last_name: str
  __ignore_type: IgnoreType | None
  __ignore_category: IgnoreCategory | None
  __ignore_term: str | None
  __job_listing: JobListing

  def __init__(self, quick_settings: QuickSettings, universal_config: UniversalConfig, job_listing: JobListing):
    self.__job_listing = job_listing
    self.__init_ignore(quick_settings, universal_config)
    self.__init_applied()

  def __init_ignore(self, quick_settings: QuickSettings, universal_config: UniversalConfig) -> None:
    self.__ignore_type = None
    self.__ignore_category = None
    self.__ignore_term = None
    self.__handle_ideal_criteria(quick_settings, universal_config)
    if not self.__ignore_type and not self.__ignore_category and not self.__ignore_term:
      self.__handle_language_ignore(universal_config)
    if not self.__ignore_type and not self.__ignore_category and not self.__ignore_term:
      self.__handle_ignore_criteria(quick_settings, universal_config)

  def __init_applied(self) -> None:
    self.__applied = (
      self.__ignore_type is None
      and self.__ignore_category is None
      and self.__ignore_term is None
    )

  def applied(self) -> bool:
    return self.__applied

  def get_first_name(self) -> str:
    return self.__first_name

  def get_last_name(self) -> str:
    return self.__last_name

  def get_ignore_type(self) -> IgnoreType | None:
    return self.__ignore_type

  def get_ignore_category(self) -> IgnoreCategory | None:
    return self.__ignore_category

  def get_ignore_term(self) -> str | None:
    return self.__ignore_term

  def get_job_listing(self) -> JobListing:
    return self.__job_listing

  def set_applied(self, applied: bool) -> None:
    self.__applied = applied

  def set_first_name(self, first_name: str) -> None:
    self.__first_name = first_name

  def set_last_name(self, last_name: str) -> None:
    self.__last_name = last_name

  def set_ignore_type(self, ignore_type: IgnoreType) -> None:
    self.__ignore_type = ignore_type

  def set_ignore_category(self, ignore_category: IgnoreCategory) -> None:
    self.__ignore_category = ignore_category

  def set_ignore_term(self, ignore_term: str) -> None:
    self.__ignore_term = ignore_term

  def set_job_listing(self, job_listing: JobListing) -> None:
    self.__job_listing = job_listing

  def __handle_ideal_criteria(self, quick_settings: QuickSettings, universal_config: UniversalConfig) -> None:
    if not quick_settings.bot_behavior.job_listing_criteria.is_in_ideal:
      return
    title = self.__job_listing.get_title().lower().strip()
    for ideal_title in universal_config.bot_behavior.ideal.titles:
      if self.__phrase_is_in_phrase(ideal_title, title):
        return
    company = self.__job_listing.get_company().lower().strip()
    for ideal_company in universal_config.bot_behavior.ideal.companies:
      if self.__phrase_is_in_phrase(ideal_company, company):
        return
    location = self.__job_listing.get_location().lower().strip()
    for ideal_location in universal_config.bot_behavior.ideal.locations:
      if self.__phrase_is_in_phrase(ideal_location, location):
        return
    logging.info("Ignoring because listing doesn't meet defined \"ideal\" criteria.")
    self.__ignore_type = IgnoreType.NOT_IN_IDEAL

  def __handle_language_ignore(self, universal_config: UniversalConfig) -> None:
    # TODO: Pull language from config
    job_listing_language = self.__job_listing.get_language().value
    if job_listing_language == Language.ENGLISH.value:
      return
    logging.info("Ignoring because listing language is: %s", job_listing_language)
    self.__ignore_type = IgnoreType.LANGUAGE
    self.__ignore_category = IgnoreCategory.LANGUAGE
    self.__ignore_term = job_listing_language

  def __handle_ignore_criteria(self, quick_settings: QuickSettings, universal_config: UniversalConfig):
    if not quick_settings.bot_behavior.job_listing_criteria.not_in_ignore:
      return
    if not self.__ignore_type and not self.__ignore_category and not self.__ignore_term:
      self.__handle_potential_title_ignore(universal_config.bot_behavior.ignore.titles)
    if not self.__ignore_type and not self.__ignore_category and not self.__ignore_term:
      self.__handle_potential_company_ignore(universal_config.bot_behavior.ignore.companies)
    if not self.__ignore_type and not self.__ignore_category and not self.__ignore_term:
      self.__handle_potential_location_ignore(universal_config.bot_behavior.ignore.locations)
    if not self.__ignore_type and not self.__ignore_category and not self.__ignore_term:
      self.__handle_potential_description_ignore(universal_config.bot_behavior.ignore.descriptions)
    if not self.__ignore_type and not self.__ignore_category and not self.__ignore_term:
      self.__handle_potential_pay_ignore(universal_config.search.salary)
    if not self.__ignore_type and not self.__ignore_category and not self.__ignore_term:
      self.__handle_potential_yoe_ignore(universal_config.bot_behavior.years_of_experience)

  def __handle_potential_title_ignore(self, ignore_titles: List | None) -> None:
    if not ignore_titles:
      return
    title = self.__job_listing.get_title().lower().strip()
    for title_to_ignore in ignore_titles:
      if self.__phrase_is_in_phrase(title_to_ignore, title):
        logging.info("Ignoring because title includes: %s", title_to_ignore)
        if isinstance(title_to_ignore, str):
          self.__ignore_type = IgnoreType.IS_IN_IGNORE
          self.__ignore_category = IgnoreCategory.TITLE
          self.__ignore_term = title_to_ignore
          return
    return

  def __handle_potential_company_ignore(self, ignore_companies: List | None) -> None:
    if not ignore_companies:
      return
    company = self.__job_listing.get_company().lower().strip()
    for company_to_ignore in ignore_companies:
      if self.__phrase_is_in_phrase(company_to_ignore, company):
        logging.info("Ignoring because company includes: %s", company_to_ignore)
        if isinstance(company_to_ignore, str):
          self.__ignore_type = IgnoreType.IS_IN_IGNORE
          self.__ignore_category = IgnoreCategory.COMPANY
          self.__ignore_term = company_to_ignore
          return

  def __handle_potential_location_ignore(self, ignore_locations: List | None) -> None:
    if not ignore_locations:
      return
    location = self.__job_listing.get_location().lower().strip()
    for location_to_ignore in ignore_locations:
      if self.__phrase_is_in_phrase(location_to_ignore, location):
        logging.info("Ignoring because location includes: %s", location_to_ignore)
        if isinstance(location_to_ignore, str):
          self.__ignore_type = IgnoreType.IS_IN_IGNORE
          self.__ignore_category = IgnoreCategory.LOCATION
          self.__ignore_term = location_to_ignore
          return

  def __handle_potential_description_ignore(self, ignore_descriptions: List | None) -> None:
    if not ignore_descriptions:
      return
    description = self.__job_listing.get_description()
    if description:
      description = description.lower().strip()
      for description_to_ignore in ignore_descriptions:
        if self.__phrase_is_in_phrase(description_to_ignore, description):
          logging.info("Ignoring because description includes: %s", description_to_ignore)
          if isinstance(description_to_ignore, str):
            self.__ignore_type = IgnoreType.IS_IN_IGNORE
            self.__ignore_category = IgnoreCategory.DESCRIPTION
            self.__ignore_term = description_to_ignore
            return

  def __handle_potential_pay_ignore(self, expected_salary: SearchSalary) -> None:
    min_pay = self.__job_listing.get_min_pay()
    max_pay = self.__job_listing.get_max_pay()
    if expected_salary.min and max_pay and expected_salary.min > max_pay:
      logging.info(
        "Job pays: %s   less than our minimum: %s",
        expected_salary.min - max_pay,
        expected_salary.min
      )
      self.__ignore_type = IgnoreType.IS_IN_IGNORE
      self.__ignore_category = IgnoreCategory.LOW_PAY
      self.__ignore_term = str(max_pay)
      return
    elif expected_salary.max and min_pay and expected_salary.max < min_pay:
      logging.info(
        "Job pays: %s   more than our maximum: %s",
        expected_salary.max - min_pay,
        expected_salary.max
      )
      self.__ignore_type = IgnoreType.IS_IN_IGNORE
      self.__ignore_category = IgnoreCategory.HIGH_PAY
      self.__ignore_term = str(min_pay)
      return

  def __handle_potential_yoe_ignore(self, years_of_experience: YearsOfExperience) -> None:
    min_yoe = self.__job_listing.get_min_yoe()
    max_yoe = self.__job_listing.get_max_yoe()
    min_yoe_desired = years_of_experience.minimum
    max_yoe_desired = years_of_experience.maximum
    if min_yoe and max_yoe_desired and max_yoe_desired < min_yoe:
      logging.info("Job requires too many Years of Experience: %s", min_yoe)
      self.__ignore_type = IgnoreType.IS_IN_IGNORE
      self.__ignore_category = IgnoreCategory.HIGH_YOE
      self.__ignore_term = str(min_yoe)
      return
    if max_yoe and min_yoe_desired and min_yoe_desired < max_yoe:
      logging.info("Job asks for too few Years of Experience: %s", max_yoe)
      self.__ignore_type = IgnoreType.IS_IN_IGNORE
      self.__ignore_category = IgnoreCategory.LOW_YOE
      self.__ignore_term = str(max_yoe)
      return

  def __phrase_is_in_phrase(self, phrase_one: str | List, phrase_two: str) -> bool:
    if isinstance(phrase_one, str):
      phrase_one = phrase_one.lower().strip()
      phrase_two = phrase_two.lower().strip()
      return self.__matches_pattern(phrase_one, phrase_two)
    elif isinstance(phrase_one, List):
      for item in phrase_one:
        if not self.__phrase_is_in_phrase(item, phrase_two):
          return False
      return True

  def __matches_pattern(self, phrase_to_ignore: str, phrase: str) -> bool:
    pattern = rf"(?<!\w)\(?{re.escape(phrase_to_ignore)}\)?(?!\w)"
    return (
      re.search(pattern, phrase) is not None
      or phrase_to_ignore == phrase
    )
