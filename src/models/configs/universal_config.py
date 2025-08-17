from dataclasses import dataclass, field
from typing import List


@dataclass
class JobMatchingList:
  titles: List[str | list] = field(default_factory=list)
  companies: List[str | list] = field(default_factory=list)
  locations: List[str | list] = field(default_factory=list)
  descriptions: List[str | list] = field(default_factory=list)

@dataclass
class YearsOfExperience:
  minimum: int | None = None
  maximum: int | None = None

@dataclass
class BotBehavior:
  pause_every_x_jobs: int = 50
  ideal: JobMatchingList = field(default_factory=JobMatchingList)
  ignore: JobMatchingList = field(default_factory=JobMatchingList)
  years_of_experience: YearsOfExperience = field(default_factory=YearsOfExperience)

@dataclass
class SearchExperience:
  entry: bool = False
  mid: bool = True
  senior: bool = False

@dataclass
class SearchLocation:
  city: str | None = None
  hybrid: bool = False
  remote: bool = True
  max_distance_in_mis: int = 0

@dataclass
class SearchSalary:
  min: int | None = None
  max: int | None = None

@dataclass
class SearchTerms:
  match: List[str] = field(default_factory=list)
  ignore: List[str] = field(default_factory=list)

@dataclass
class SearchMisc:
  min_company_rating: float | None = None

@dataclass
class Search:
  experience: SearchExperience = field(default_factory=SearchExperience)
  location: SearchLocation = field(default_factory=SearchLocation)
  salary: SearchSalary = field(default_factory=SearchSalary)
  terms: SearchTerms = field(default_factory=SearchTerms)
  misc: SearchMisc = field(default_factory=SearchMisc)

@dataclass
class UniversalConfig:
  bot_behavior: BotBehavior = field(default_factory=BotBehavior)
  search: Search = field(default_factory=Search)
