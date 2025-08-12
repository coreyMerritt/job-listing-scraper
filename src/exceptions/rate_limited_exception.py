from models.enums.platform import Platform


class RateLimitedException(Exception):
  __platform: Platform

  def __init__(self, platform: Platform, message="Rate Limited."):
    super().__init__(message)
    self.__platform = platform

  def get_platform(self) -> Platform:
    return self.__platform
