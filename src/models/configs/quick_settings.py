from dataclasses import dataclass, field


@dataclass
class MaxAge:
  years: float = 0
  months: float = 0
  weeks: float = 1
  days: float = 0
  hours: float = 0
  minutes: float = 0
  seconds: float = 0

@dataclass
class JobListingCriteria:
  not_in_ignore: bool = True
  is_in_ideal: bool = False
  max_age: MaxAge = field(default_factory=MaxAge)

@dataclass
class BotBehavior:
  fallback_to_brief_on_load_issues: bool = True
  full_scrape: bool = False
  job_listing_criteria: JobListingCriteria = field(default_factory=JobListingCriteria)
  default_page_load_timeout: int = 30
  platform_order: list = field(default_factory=list)

@dataclass
class QuickSettings:
  bot_behavior: BotBehavior = field(default_factory=BotBehavior)
