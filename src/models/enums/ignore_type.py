from enum import Enum


class IgnoreType(Enum):
  IS_IN_IGNORE = "Meets ignore criteria"
  NOT_IN_IDEAL = "Doesn't meet ideal criteria"
  LANGUAGE = "Language mismatch"
  DESCRIPTION_DIDNT_LOAD = "Job description didnt load"
