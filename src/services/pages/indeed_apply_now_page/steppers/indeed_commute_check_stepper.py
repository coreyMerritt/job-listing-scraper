import undetected_chromedriver as uc


class IndeedCommuteCheckStepper:
  __driver: uc.Chrome

  def __init__(
    self,
    driver: uc.Chrome
  ):
    self.__driver = driver

  def is_present(self) -> bool:
    COMMUTE_CHECK_URL = "smartapply.indeed.com/beta/indeedapply/form/commute-check"
    return COMMUTE_CHECK_URL in self.__driver.current_url

  def resolve(self) -> None:
    pass # ???
