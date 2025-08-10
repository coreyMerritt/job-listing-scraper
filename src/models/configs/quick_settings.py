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
  pause_on_unknown_stepper: bool = False
  pause_after_each_platform: bool = False
  remove_tabs_after_each_platform: bool = True
  default_page_load_timeout: int = 30
  pause_every_x_jobs: int | None = None
  platform_order: list = field(default_factory=list)

@dataclass
class QuickSettings:
  bot_behavior: BotBehavior = field(default_factory=BotBehavior)
