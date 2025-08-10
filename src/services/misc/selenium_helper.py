import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from models.configs.system_config import SystemConfig
from models.enums.element_type import ElementType
from services.misc.proxy_manager import ProxyManager


class SeleniumHelper:
  __driver: uc.Chrome
  __system_config: SystemConfig
  __default_page_load_timeout: int
  __proxy_manager: ProxyManager

  def __init__(
    self,
    system_config: SystemConfig,
    default_page_load_timeout: int,
    proxy_manager: ProxyManager
  ):
    self.__system_config = system_config
    self.__default_page_load_timeout = default_page_load_timeout
    self.__proxy_manager = proxy_manager
    self.__driver = self.get_new_driver()
    self.__driver.set_page_load_timeout(default_page_load_timeout)

  def get_driver(self) -> uc.Chrome:
    return self.__driver

  def get_new_driver(self) -> uc.Chrome:
    logging.debug("Getting a new driver...")
    options = uc.ChromeOptions()
    options.binary_location = self.__system_config.browser.path
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--force-dark-mode")
    self.__handle_proxy_configuration(options)
    driver = uc.Chrome(options=options)
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")
    return driver

  def set_driver_timeout_to_default(self) -> None:
    self.__driver.set_page_load_timeout(self.__default_page_load_timeout)

  def open_new_tab(self) -> None:
    self.__driver.execute_script("window.open('about:blank', '_blank');")
    self.__driver.switch_to.window(self.__driver.window_handles[-1])

  def text_is_present(
    self,
    some_text: str,
    element_type: ElementType,
    base_element: WebElement | None = None
  ) -> bool:
    logging.debug("Checking if visible text is present: %s", some_text)
    some_text = some_text.lower().strip()
    if base_element:
      elements = base_element.find_elements(By.TAG_NAME, element_type.value)
    else:
      elements = self.__driver.find_elements(By.TAG_NAME, element_type.value)
    for el in elements:
      try:
        if el.is_displayed():
          visible_text = (el.text or "").lower().strip()
          if some_text in visible_text:
            return True
      except StaleElementReferenceException:
        continue
    return False

  def exact_text_is_present(
    self,
    some_text: str,
    element_type: ElementType,
    base_element: WebElement | None = None
  ) -> bool:
    logging.debug("Checking if visible text is present: %s", some_text)
    some_text = some_text.lower().strip()
    if base_element:
      elements = base_element.find_elements(By.TAG_NAME, element_type.value)
    else:
      elements = self.__driver.find_elements(By.TAG_NAME, element_type.value)
    for el in elements:
      try:
        if el.is_displayed():
          visible_text = (el.text or "").lower().strip()
          if some_text == visible_text:
            return True
      except StaleElementReferenceException:
        continue
    return False

  def get_element_by_text(
    self,
    some_text: str,
    element_type: ElementType,
    base_element: WebElement | None = None
  ) -> WebElement:
    logging.debug("Getting %s with text: %s", element_type.value, some_text)
    some_text = some_text.lower().strip()
    if base_element:
      elements = base_element.find_elements(By.TAG_NAME, element_type.value)
    else:
      elements = self.__driver.find_elements(By.TAG_NAME, element_type.value)
    for el in elements:
      try:
        visible_text = (el.text or "").lower().strip()
        if some_text in visible_text:
          return el
      except StaleElementReferenceException:
        continue
    raise NoSuchElementException(f"Failed to find {element_type.value} with text: {some_text}")

  def get_element_by_exact_text(
    self,
    some_text: str,
    element_type: ElementType,
    base_element: WebElement | None = None
  ) -> WebElement:
    logging.debug("Getting %s with text: %s", element_type.value, some_text)
    some_text = some_text.lower().strip()
    if base_element:
      elements = base_element.find_elements(By.TAG_NAME, element_type.value)
    else:
      elements = self.__driver.find_elements(By.TAG_NAME, element_type.value)
    for el in elements:
      try:
        visible_text = (el.text or "").lower().strip()
        if some_text == visible_text:
          return el
      except StaleElementReferenceException:
        continue
    raise NoSuchElementException(f"Failed to find {element_type.value} with text: {some_text}")

  def exact_aria_label_is_present(
    self,
    some_aria_label: str,
    base_element: WebElement | None = None
  ) -> bool:
    selector = f'[aria-label="{some_aria_label}"]'
    try:
      if base_element:
        base_element.find_element(By.CSS_SELECTOR, selector)
      else:
        self.__driver.find_element(By.CSS_SELECTOR, selector)
      return True
    except NoSuchElementException:
      return False


  def get_element_by_aria_label(
    self,
    some_aria_label: str,
    base_element: WebElement | None = None
  ) -> WebElement:
    selector = f'[aria-label="{some_aria_label}"]'
    if base_element:
      element = base_element.find_element(By.CSS_SELECTOR, selector)
    else:
      element = self.__driver.find_element(By.CSS_SELECTOR, selector)
    return element

  def write_to_input(self, some_text: str, input_el: WebElement, sensitive=False) -> None:
    if sensitive:
      logging.debug("Writing: %s to input...", "*" * len(some_text))
    else:
      logging.debug("Writing: %s to input...", some_text)
    if input_el.text.lower().strip() != some_text.lower().strip():
      input_el.send_keys(Keys.CONTROL + "a")
      input_el.send_keys(Keys.BACKSPACE)
      input_el.send_keys(some_text)

  def write_to_select(self, some_text: str, select_el: WebElement) -> None:
    logging.debug("Selecting: %s from dropdown...", some_text)
    self.__driver.execute_script("""
      const el = arguments[0];
      el.value = arguments[1];
      el.dispatchEvent(new Event('change'));
    """, select_el, some_text)

  def check_box_by_name(self, some_name: str, checked: bool = True) -> None:
    logging.debug("Setting checkbox %s to %s", some_name, checked)
    checkbox = self.__driver.find_element(By.NAME, some_name)
    if checked:
      self.__driver.execute_script("arguments[0].checked = true;", checkbox)
    else:
      self.__driver.execute_script("arguments[0].checked = false;", checkbox)

  def scroll_down(self, element: WebElement | None = None, pixels=50) -> None:
    if element:
      self.__driver.execute_script("arguments[0].scrollBy(0, arguments[1]);", element, pixels)
    else:
      self.__driver.execute_script("window.scrollBy(0, arguments[0]);", pixels)

  def scroll_to_bottom(self, element: WebElement | None = None) -> None:
    if element:
      self.__driver.execute_script("arguments[0].scrollTo(0, document.body.scrollHeight);", element)
    else:
      self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

  def scroll_into_view(self, element: WebElement) -> None:
    self.__driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    self.scroll_down(element)

  def __handle_proxy_configuration(self, options: uc.ChromeOptions) -> uc.ChromeOptions:
    proxy_config = self.__proxy_manager.get_best_proxy()
    if proxy_config:
      logging.info("Using proxy: %s", proxy_config.host)
      options.add_argument(f"--proxy-server=socks5://{proxy_config.host}:{proxy_config.port}")
    return options
