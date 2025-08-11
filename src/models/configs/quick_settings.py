from dataclasses import dataclass, field


@dataclass
class ApplicationCriteria:
  not_in_ignore: bool = True
  is_in_ideal: bool = False


@dataclass
class BotBehavior:
  full_scrape: bool = False
  job_listing_criteria: ApplicationCriteria = field(default_factory=ApplicationCriteria)
  default_page_load_timeout: int = 30
  platform_order: list = field(default_factory=list)

@dataclass
class QuickSettings:
  bot_behavior: BotBehavior = field(default_factory=BotBehavior)
