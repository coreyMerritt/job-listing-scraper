import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException
from models.configs.universal_config import UniversalConfig
from models.enums.element_type import ElementType
from services.misc.selenium_helper import SeleniumHelper


class LinkedinResumeStepper:
  __driver: uc.Chrome
  __selenium_helper: SeleniumHelper
  __universal_config: UniversalConfig
  __context_element: WebElement
  __relative_resume_list_div_xpath: str

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    universal_config: UniversalConfig,
    # This is the default to be used when on the genuine resume stepper
    # Overriding this is allowed to implement DRY because the contact info stepper
    # occassionally also handles resume selection... Heckin' Linkedin...
    relative_resume_list_div_xpath: str = "./div[2]/div/div[2]/form/div/div/div/div[1]"
  ):
    self.__driver = driver
    self.__selenium_helper = selenium_helper
    self.__universal_config = universal_config
    self.__relative_resume_list_div_xpath = relative_resume_list_div_xpath

  def set_context(self, context_element: WebElement) -> None:
    self.__context_element = context_element

  def is_present(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Resume",
      ElementType.H3,
      self.__context_element
    )

  def resolve(self) -> None:
    if self.__is_compensation_label():
      self.__handle_compensation()
    if self.__is_country_label():
      self.__handle_country()
    if self.__is_summary_label():
      self.__handle_summary()
    if self.__is_us_authorization_span():
      self.__handle_us_authorization_question()
    if self.__is_github_profile_label():
      self.__handle_github_profile_question()
    if self.__is_relocation_span():
      self.__handle_relocation_question()
    if self.__is_vague_previously_employed_by_us_label():
      self.__handle_vague_previously_employed_by_us_question()
    if self.__is_vague_salary_requirements_question():
      self.__handle_vague_salary_requirements_question()
    if self.__is_vague_education_completed_question():
      self.__handle_vague_education_completed_question()
    self.__handle_resume()
    if self.__cover_letter_is_required():
      self.__handle_cover_letter()

  def __handle_resume(self) -> None:
    expected_resume_name = self.__build_expected_resume_name()
    available_resume_count = self.__count_available_resumes()
    for i in range(1, available_resume_count + 1):
      current_resume_name = self.__get_resume_name(i)
      if current_resume_name.lower().strip() == expected_resume_name.lower().strip():
        current_resume_span = self.__get_resume_span(i)
        if not "Deselect" in current_resume_span.text:
          current_resume_span.click()
        return
    raise RuntimeError("Failed to find a suitable resume to select.")

  def __get_resumes_div(self) -> WebElement:
    resumes_div = self.__context_element.find_element(By.XPATH, self.__relative_resume_list_div_xpath)
    return resumes_div

  def __build_expected_resume_name(self) -> str:
    first_name = self.__universal_config.about_me.name.first
    last_name = self.__universal_config.about_me.name.last
    resume_name = f"{first_name}-{last_name}.pdf"
    return resume_name

  def __count_available_resumes(self) -> int:
    MAX_INT_32 = 2_147_483_647
    resumes_div = self.__get_resumes_div()
    for i in range(1, MAX_INT_32):
      relative_resume_div_xpath = f"./div[{i}]"
      try:
        resumes_div.find_element(By.XPATH, relative_resume_div_xpath)
        continue
      except NoSuchElementException:
        return i - 1
    raise RuntimeError("Counted indefinitely while trying to count available resumes.")

  def __get_resume_div(self, i: int) -> WebElement:
    resumes_div = self.__get_resumes_div()
    relative_resume_div_xpath = f"./div[{i}]"
    current_resume_div = resumes_div.find_element(By.XPATH, relative_resume_div_xpath)
    return current_resume_div

  def __get_resume_name(self, i: int) -> str:
    current_resume_div = self.__get_resume_div(i)
    relative_current_resume_name_h3_xpath = "./p/h3"
    current_resume_name_h3 = current_resume_div.find_element(By.XPATH, relative_current_resume_name_h3_xpath)
    current_resume_name = current_resume_name_h3.text
    return current_resume_name

  def __get_resume_span(self, i: int) -> WebElement:
    # This resume span is the pseudo-radio-button that selects the resume
    resume_div = self.__get_resume_div(i)
    relative_resume_span_xpath = "./div/label/span"
    resume_span = resume_div.find_element(By.XPATH, relative_resume_span_xpath)
    return resume_span

  def __is_compensation_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "What are your annual total compensation requirements?",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_compensation(self) -> None:
    assert self.__is_compensation_label()
    minimum_compensation = self.__universal_config.search.salary.min
    maximum_compensation = self.__universal_config.search.salary.max
    expected_compensation = round(((maximum_compensation + minimum_compensation) / 2) * 1.1, -3)
    compensation_label = self.__selenium_helper.get_element_by_exact_text(
      "What are your annual total compensation requirements?",
      ElementType.LABEL,
      self.__context_element
    )
    compensation_input = self.__get_input_from_label(compensation_label)
    self.__selenium_helper.write_to_input(str(expected_compensation), compensation_input)

  def __is_country_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Country:",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_country(self) -> None:
    assert self.__is_country_label()
    country = self.__universal_config.about_me.location.country
    country_label = self.__selenium_helper.get_element_by_exact_text(
      "Country:",
      ElementType.LABEL,
      self.__context_element
    )
    country_input = self.__get_input_from_label(country_label)
    self.__selenium_helper.write_to_input(country, country_input)

  def __is_summary_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Summary",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_summary(self) -> None:
    assert self.__is_summary_label()
    summary = ""
    for experience in self.__universal_config.about_me.work_experience:
      summary += experience.title
      summary += f"\n{experience.company}"
      summary += f"\n{experience.start.year}/{experience.start.month} - {experience.end.year}/{experience.end.month}"
      summary += "\n\n"
    summary_label = self.__selenium_helper.get_element_by_exact_text(
      "Summary",
      ElementType.LABEL,
      self.__context_element
    )
    summary_textarea = summary_label.find_element(By.XPATH, "../textarea")
    self.__selenium_helper.write_to_input(summary, summary_textarea)

  def __is_us_authorization_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Authorized/Eligible to work in the US now and in the future?*",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_us_authorization_question(self) -> None:
    assert self.__is_us_authorization_span()
    authorized = self.__universal_config.about_me.authorized_to_work_in_us
    us_auth_span = self.__selenium_helper.get_element_by_exact_text(
      "Authorized/Eligible to work in the US now and in the future?*",
      ElementType.SPAN,
      self.__context_element
    )
    us_auth_select = Select(us_auth_span.find_element(By.XPATH, "../../select"))
    if authorized:
      us_auth_select.select_by_value("Yes")
    else:
      us_auth_select.select_by_value("No")

  def __is_github_profile_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Please provide your GitHub Profile",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_github_profile_question(self) -> None:
    assert self.__is_github_profile_label()
    github_link = self.__universal_config.about_me.links.github
    github_label = self.__selenium_helper.get_element_by_exact_text(
      "Please provide your GitHub Profile",
      ElementType.LABEL,
      self.__context_element
    )
    github_textarea = github_label.find_element(By.XPATH, "../textarea")
    self.__selenium_helper.write_to_input(github_link, github_textarea)

  def __is_relocation_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Will you need to relocate for this position?",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_relocation_question(self) -> None:
    willing_to_relocate = self.__universal_config.about_me.willing_to_relocate
    relocation_span = self.__selenium_helper.get_element_by_exact_text(
      "Will you need to relocate for this position?",
      ElementType.SPAN,
      self.__context_element
    )
    relocation_fieldset = relocation_span.find_element(By.XPATH, "../../..")
    if willing_to_relocate:
      willing_to_relocate_label = relocation_fieldset.find_element(By.XPATH, "./div[1]/label")
      willing_to_relocate_label.click()
    else:
      not_willing_to_relocate_label = relocation_fieldset.find_element(By.XPATH, "./div[2]/label")
      not_willing_to_relocate_label.click()

  def __is_vague_previously_employed_by_us_label(self) -> bool:
    return self.__selenium_helper.text_is_present(
      "previously employed by",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_vague_previously_employed_by_us_question(self) -> None:
    previously_employed_label = self.__selenium_helper.get_element_by_text(
      "previously employed by",
      ElementType.LABEL,
      self.__context_element
    )
    previously_employed_input = previously_employed_label.find_element(By.XPATH, "../input")
    self.__selenium_helper.write_to_input("No", previously_employed_input)

  def __is_vague_salary_requirements_question(self) -> bool:
    return self.__selenium_helper.text_is_present(
      "salary requirements",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_vague_salary_requirements_question(self) -> None:
    minimum_compensation = self.__universal_config.search.salary.min
    maximum_compensation = self.__universal_config.search.salary.max
    expected_compensation = round(((maximum_compensation + minimum_compensation) / 2) * 1.1, -3)
    salary_requirements_label = self.__selenium_helper.get_element_by_text(
      "salary requirements",
      ElementType.LABEL,
      self.__context_element
    )
    salary_requirements_input = salary_requirements_label.find_element(By.XPATH, "../input")
    self.__selenium_helper.write_to_input(str(expected_compensation), salary_requirements_input)

  def __is_vague_education_completed_question(self) -> bool:
    return self.__selenium_helper.text_is_present(
      "Highest Level of Education Completed",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_vague_education_completed_question(self) -> None:
    degrees = self.__universal_config.about_me.education.degrees
    education_completed_label = self.__selenium_helper.get_element_by_text(
      "Highest Level of Education Completed",
      ElementType.LABEL,
      self.__context_element
    )
    education_completed_input = education_completed_label.find_element(By.XPATH, "../input")
    self.__selenium_helper.write_to_input(degrees[0].degree_type, education_completed_input)

  def __cover_letter_is_required(self) -> bool:
    try:
      label = self.__selenium_helper.get_element_by_exact_text(
        "Cover letter",
        ElementType.LABEL,
        self.__context_element
      )
    except NoSuchElementException:
      try:
        label = self.__selenium_helper.get_element_by_exact_text(
          "Be sure to include an updated cover letter",
          ElementType.SPAN,
          self.__context_element
        )
      except NoSuchElementException:
        return False
    after_content = self.__driver.execute_script("""
      const el = arguments[0];
      const style = window.getComputedStyle(el, '::after');
      return style.getPropertyValue('content');
    """, label)
    if after_content and after_content != "none":
      print(f"DEBUG: after_content: {after_content}")
      input("DEBUG: Cover letter is required.")
      return True
    return False

  def __handle_cover_letter(self) -> None:
    if self.__universal_config.bot_behavior.ignore_jobs_that_demand_cover_letters:
      self.__driver.close()
      self.__driver.switch_to.window(self.__driver.window_handles[0])
    else:
      self.__driver.switch_to.window(self.__driver.window_handles[0])

  def __get_input_from_label(self, label: WebElement) -> WebElement:
    input_id = label.get_attribute("for")
    if input_id:
      input_el = self.__context_element.find_element(By.ID, input_id)
      return input_el
    raise NoSuchElementException("Invalid label_text.")
