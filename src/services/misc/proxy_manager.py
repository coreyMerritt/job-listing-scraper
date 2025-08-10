from typing import List
from models.configs.system_config import ProxyConfig
from models.enums.platform import Platform
from services.misc.database_manager import DatabaseManager


class ProxyManager:
  __database_manager: DatabaseManager
  __current_proxy: ProxyConfig
  __potential_proxies: List[ProxyConfig]

  def __init__(self, proxies: List[ProxyConfig], database_manager: DatabaseManager):
    self.__database_manager = database_manager
    self.__potential_proxies = proxies

  def log_rate_limit_block(self, platform: Platform) -> None:
    self.__database_manager.log_rate_limit_block(self.__current_proxy.host, platform)

  def get_best_proxy(self, platform: Platform | None = None) -> ProxyConfig | None:
    greatest_time_delta = {}
    for i, proxy in enumerate(self.__potential_proxies):
      if i == 0:
        time_delta = self.__database_manager.get_rate_limit_time_delta(proxy.host, platform)
        greatest_time_delta = {
          "time_delta": time_delta,
          "proxy_config": proxy
        }
        continue
      time_delta = self.__database_manager.get_rate_limit_time_delta(proxy.host, platform)
      if greatest_time_delta["time_delta"] < time_delta:
        greatest_time_delta["time_delta"] = time_delta
        greatest_time_delta["proxy_config"] = proxy
    self.__current_proxy = greatest_time_delta["proxy_config"]
    return greatest_time_delta["proxy_config"]
