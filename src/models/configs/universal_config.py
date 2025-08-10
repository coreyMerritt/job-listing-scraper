from dataclasses import dataclass, field
from typing import List


@dataclass
class AboutMeName:
  first: str = ""
  last: str = ""

@dataclass
class AboutMeContact:
  email_address: str = ""
  phone_number: str = ""

@dataclass
class AboutMeLocation:
  city: str = ""
  country: str = ""
  postal_code: int = 00000
  state: str = ""
  state_code: str = ""
  street_address: str = ""

@dataclass
class Date:
  day_of_month: int = 0
  month: int = 0
  year: int = 0

@dataclass
class WorkExperience:
  title: str
  company: str
  currently_work_here: bool
  start: Date = field(default_factory=Date)
  end: Date = field(default_factory=Date)

@dataclass
class Degree:
  currently_attending: bool = False
  school: str = ""
  city: str = ""
  state: str = ""
  country: str = ""
  degree_type: str = ""
  field_of_study: str = ""
  start: Date = field(default_factory=Date)
  end: Date = field(default_factory=Date)

@dataclass
class Education:
  degrees: List[Degree] = field(default_factory=list)

@dataclass
class Links:
  github: str = ""

@dataclass
class AboutMe:
  authorized_to_work_in_us: bool = True
  military_veteran: bool = False
  willing_to_relocate: bool = True
  links: Links = field(default_factory=Links)
  name: AboutMeName = field(default_factory=AboutMeName)
  contact: AboutMeContact = field(default_factory=AboutMeContact)
  location: AboutMeLocation = field(default_factory=AboutMeLocation)
  work_experience: List[WorkExperience] = field(default_factory=list)
  education: Education = field(default_factory=Education)

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
  ignore_jobs_that_demand_cover_letters: bool = False
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
  min: int = 30000
  max: int = 300000

@dataclass
class SearchTerms:
  match: List[str] = field(default_factory=list)
  ignore: List[str] = field(default_factory=list)

@dataclass
class SearchMisc:
  max_age_in_days: int = 7
  min_company_rating: float = 3.0

@dataclass
class Search:
  experience: SearchExperience = field(default_factory=SearchExperience)
  location: SearchLocation = field(default_factory=SearchLocation)
  salary: SearchSalary = field(default_factory=SearchSalary)
  terms: SearchTerms = field(default_factory=SearchTerms)
  misc: SearchMisc = field(default_factory=SearchMisc)

@dataclass
class UniversalConfig:
  about_me: AboutMe = field(default_factory=AboutMe)
  bot_behavior: BotBehavior = field(default_factory=BotBehavior)
  search: Search = field(default_factory=Search)
