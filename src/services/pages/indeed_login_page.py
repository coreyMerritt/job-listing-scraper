import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from models.configs.indeed_config import IndeedConfig
from models.enums.element_type import ElementType
from services.misc.selenium_helper import SeleniumHelper


class IndeedLoginPage:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __indeed_config: IndeedConfig

  def __init__(self, driver: uc.Chrome, selenium_helper: SeleniumHelper, indeed_config: IndeedConfig):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__indeed_config = indeed_config

  def login(self) -> None:
    self.__write_email_to_vague_input()
    self.__click_continue_button()

  def __write_email_to_vague_input(self) -> None:
    email_address = self.__indeed_config.email
    email_address_label = self.__selenium_helper.get_element_by_text(
      "Email address",
      ElementType.LABEL
    )
    email_address_input = email_address_label.find_element(By.XPATH, "../span/input")
    self.__selenium_helper.write_to_input(email_address, email_address_input)

  def __click_continue_button(self) -> None:
    continue_button_xpath = "/html/body/div/div[2]/main/div/div/div[2]/div/form/button"
    continue_button = self.__driver.find_element(By.XPATH, continue_button_xpath)
    continue_button.click()
