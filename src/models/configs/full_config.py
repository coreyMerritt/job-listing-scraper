from dataclasses import dataclass, field
from models.configs.glassdoor_config import GlassdoorConfig
from models.configs.indeed_config import IndeedConfig
from models.configs.linkedin_config import LinkedinConfig
from models.configs.quick_settings import QuickSettings
from models.configs.system_config import SystemConfig
from models.configs.universal_config import UniversalConfig


@dataclass
class FullConfig:
  glassdoor: GlassdoorConfig = field(default_factory=GlassdoorConfig)
  indeed: IndeedConfig = field(default_factory=IndeedConfig)
  linkedin: LinkedinConfig = field(default_factory=LinkedinConfig)
  quick_settings: QuickSettings = field(default_factory=QuickSettings)
  system: SystemConfig = field(default_factory=SystemConfig)
  universal: UniversalConfig = field(default_factory=UniversalConfig)
