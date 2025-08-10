from dataclasses import dataclass, field


@dataclass
class ApplicationCriteria:
  not_in_ignore: bool = True
  is_in_ideal: bool = False

@dataclass
class EasyApplyOnly:
  glassdoor: bool = True
  indeed: bool = True
  linkedin: bool = True

@dataclass
class BotBehavior:
  application_criteria: ApplicationCriteria = field(default_factory=ApplicationCriteria)
  easy_apply_only: EasyApplyOnly = field(default_factory=EasyApplyOnly)
  default_page_load_timeout: int = 30
  platform_order: list = field(default_factory=list)

@dataclass
class QuickSettings:
  bot_behavior: BotBehavior = field(default_factory=BotBehavior)
