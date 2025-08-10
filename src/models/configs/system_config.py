from dataclasses import dataclass, field
from typing import List


@dataclass
class DatabaseConfig:
  engine: str = ""
  username: str = ""
  password: str = ""
  host: str = ""
  port: int = 3306
  name: str = ""

@dataclass
class BrowserConfig:
  path: str = ""

@dataclass
class ProxyConfig:
  host: str
  port: int

@dataclass
class SystemConfig:
  browser: BrowserConfig = field(default_factory=BrowserConfig)
  database: DatabaseConfig = field(default_factory=DatabaseConfig)
  proxies: List[ProxyConfig] = field(default_factory=list)
