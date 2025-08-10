from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By


class GlassdoorShowMoreJobsButton:
  __instance: WebElement

  def __init__(self, job_listings_ul: WebElement):
    self.__instance = job_listings_ul.find_element(By.XPATH, "../div/div/button")

  def get_raw_web_element(self) -> WebElement:
    return self.__instance

  def click(self) -> None:
    self.__instance.click()
