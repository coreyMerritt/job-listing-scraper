from enum import Enum


class IgnoreCategory(Enum):
  LANGUAGE = "Language"
  TITLE = "Title"
  COMPANY = "Company"
  LOCATION = "Location"
  DESCRIPTION = "Description"
  LOW_PAY = "Low Pay"
  HIGH_PAY = "High Pay"
  LOW_YOE = "Low YoE"
  HIGH_YOE = "High YoE"
