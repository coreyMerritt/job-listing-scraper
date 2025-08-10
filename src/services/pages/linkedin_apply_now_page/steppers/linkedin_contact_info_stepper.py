import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.select import Select
from models.enums.element_type import ElementType
from models.configs.linkedin_config import LinkedinConfig
from models.configs.universal_config import UniversalConfig
from services.misc.selenium_helper import SeleniumHelper
from services.pages.linkedin_apply_now_page.steppers.linkedin_resume_stepper import LinkedinResumeStepper


class LinkedinContactInfoStepper:
  __selenium_helper: SeleniumHelper
  __linkedin_config: LinkedinConfig
  __universal_config: UniversalConfig
  __context_element: WebElement
  __resume_stepper: LinkedinResumeStepper

  def __init__(
    self,
    driver: uc.Chrome,
    selenium_helper: SeleniumHelper,
    universal_config: UniversalConfig,
    linkedin_config: LinkedinConfig
  ):
    self.__selenium_helper = selenium_helper
    self.__linkedin_config = linkedin_config
    self.__universal_config = universal_config
    self.__resume_stepper = LinkedinResumeStepper(
      driver,
      selenium_helper,
      universal_config,
      "./div[2]/div/div/form/div/div[2]/div/div[1]"
    )

  def set_context(self, context_element: WebElement) -> None:
    self.__context_element = context_element

  def is_present(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Contact info",
      ElementType.H3,
      self.__context_element
    )

  def resolve(self) -> None:
    logging.debug("Handling Contact Info page...")
    if self.__is_first_name_label():
      self.__handle_first_name()
    if self.__is_last_name_label():
      self.__handle_last_name()
    if self.__is_country_code_label():
      self.__handle_country_code()
      self.__remove_suggestion_dialogs()
    if self.__is_mobile_phone_number_label():
      self.__handle_mobile_phone_number_field()
    if self.__is_phone_label():
      self.__handle_phone_field()
    if self.__is_email_address_label():
      self.__handle_email_address()
    if self.__is_location_label():
      self.__handle_location()
    if self.__is_street_address_label():
      self.__handle_street_address()
    if self.__is_city_label():
      self.__handle_city()
    if self.__is_state_or_region_label():
      self.__handle_state_or_region()
    if self.__is_zip_or_postal_code_label():
      self.__handle_zip_or_postal_code()
    if self.__is_country_span():
      self.__handle_country()
    if self.__is_willing_to_relocate_select():
      self.__handle_willing_to_relocate_select()
    if self.__is_us_authorization_question_span():
      self.__handle_us_authorization_question()
    if self.__is_resume_selection_div():
      self.__resume_stepper.set_context(self.__context_element)
      self.__resume_stepper.resolve()
    if self.__is_referral_span():
      self.__handle_referral_question()
    if self.__is_city_state_zip_label():
      self.__handle_city_state_zip()
    if self.__is_preferred_name_label():
      self.__handle_preferred_name()
    self.__remove_suggestion_dialogs()

  def __is_first_name_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "First name",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_first_name(self) -> None:
    assert self.__is_first_name_label()
    first_name = self.__universal_config.about_me.name.first
    first_name_label = self.__selenium_helper.get_element_by_exact_text(
      "First name",
      ElementType.LABEL,
      self.__context_element
    )
    first_name_input = self.__get_input_from_label(first_name_label)
    self.__selenium_helper.write_to_input(first_name, first_name_input)

  def __is_last_name_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Last name",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_last_name(self) -> None:
    assert self.__is_last_name_label()
    last_name = self.__universal_config.about_me.name.last
    last_name_label = self.__selenium_helper.get_element_by_exact_text(
      "Last name",
      ElementType.LABEL,
      self.__context_element
    )
    last_name_input = self.__get_input_from_label(last_name_label)
    self.__selenium_helper.write_to_input(last_name, last_name_input)

  def __is_country_code_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Phone country code",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_country_code(self) -> None:
    assert self.__is_country_code_label()
    country = self.__universal_config.about_me.location.country
    phone_number_country_code_span = self.__selenium_helper.get_element_by_exact_text(
      "Phone country code",
      ElementType.SPAN,
      self.__context_element
    )
    phone_number_country_code_select = self.__get_select_from_span(phone_number_country_code_span)
    desired_country_option = self.__selenium_helper.get_element_by_exact_text(
      country,
      ElementType.OPTION,
      self.__context_element
    )
    phone_number_country_code_select.select_by_visible_text(desired_country_option.text)
    desired_country_option = self.__selenium_helper.get_element_by_exact_text(
      country,
      ElementType.OPTION,
      self.__context_element
    )
    desired_country_option.click()

  def __is_mobile_phone_number_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Mobile phone number",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_mobile_phone_number_field(self) -> None:
    phone_number = self.__universal_config.about_me.contact.phone_number
    mobile_phone_number_label = self.__selenium_helper.get_element_by_exact_text(
      "Mobile phone number",
      ElementType.LABEL,
      self.__context_element
    )
    mobile_phone_number_input = self.__get_input_from_label(mobile_phone_number_label)
    self.__selenium_helper.write_to_input(phone_number, mobile_phone_number_input)

  def __is_phone_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Phone",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_phone_field(self) -> None:
    phone_number = self.__universal_config.about_me.contact.phone_number
    phone_label = self.__selenium_helper.get_element_by_exact_text(
      "Phone",
      ElementType.LABEL,
      self.__context_element
    )
    phone_input = self.__get_input_from_label(phone_label)
    self.__selenium_helper.write_to_input(phone_number, phone_input)

  def __is_email_address_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Email address",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_email_address(self) -> None:
    assert self.__is_email_address_label()
    email_address = self.__linkedin_config.email
    email_address_span = self.__selenium_helper.get_element_by_exact_text(
      "Email address",
      ElementType.SPAN,
      self.__context_element
    )
    email_address_select = self.__get_select_from_span(email_address_span)
    desired_email_address_option = self.__selenium_helper.get_element_by_exact_text(
      email_address,
      ElementType.OPTION,
      self.__context_element
    )
    email_address_select.select_by_visible_text(desired_email_address_option.text)
    desired_email_address_option.click()

  def __is_location_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Location (city)",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_location(self) -> None:
    assert self.__is_location_label()
    location = f"{self.__universal_config.about_me.location.city}, {self.__universal_config.about_me.location.state}, {self.__universal_config.about_me.location.country}"    # pylint: disable=line-too-long
    location_span = self.__selenium_helper.get_element_by_exact_text(
      "Location (city)",
      ElementType.SPAN,
      self.__context_element
    )
    location_label = location_span.find_element(By.XPATH, "..")
    location_input = self.__get_input_from_label(location_label)
    self.__selenium_helper.write_to_input(location, location_input)
    while str(location_input.get_attribute("aria-expanded")).lower().strip() == "true":
      location_input.send_keys(Keys.TAB)

  def __is_street_address_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Street Address",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_street_address(self) -> None:
    assert self.__is_street_address_label()
    street_address = self.__universal_config.about_me.location.street_address
    street_address_label = self.__selenium_helper.get_element_by_exact_text(
      "Street Address",
      ElementType.LABEL,
      self.__context_element
    )
    street_address_input = self.__get_input_from_label(street_address_label)
    self.__selenium_helper.write_to_input(street_address, street_address_input)

  def __is_city_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "City",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_city(self) -> None:
    assert self.__is_city_label()
    city = self.__universal_config.about_me.location.city
    city_label = self.__selenium_helper.get_element_by_exact_text(
      "City",
      ElementType.LABEL,
      self.__context_element
    )
    city_input = self.__get_input_from_label(city_label)
    self.__selenium_helper.write_to_input(city, city_input)
    while str(city_input.get_attribute("aria-expanded")).lower().strip() == "true":
      city_input.send_keys(Keys.TAB)

  def __is_state_or_region_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "State or Region",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_state_or_region(self) -> None:
    assert self.__is_state_or_region_label()
    state = self.__universal_config.about_me.location.state
    state_or_region_label = self.__selenium_helper.get_element_by_exact_text(
      "State or Region",
      ElementType.LABEL,
      self.__context_element
    )
    state_or_region_input = self.__get_input_from_label(state_or_region_label)
    self.__selenium_helper.write_to_input(state, state_or_region_input)

  def __is_zip_or_postal_code_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Zip or Postal Code",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_zip_or_postal_code(self) -> None:
    assert self.__is_zip_or_postal_code_label()
    postal_code = self.__universal_config.about_me.location.postal_code
    zip_or_postal_code_label = self.__selenium_helper.get_element_by_exact_text(
      "Zip or Postal Code",
      ElementType.LABEL,
      self.__context_element
    )
    zip_or_postal_code_input = self.__get_input_from_label(zip_or_postal_code_label)
    self.__selenium_helper.write_to_input(str(postal_code), zip_or_postal_code_input)

  def __is_country_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Country",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_country(self) -> None:
    assert self.__is_country_span()
    country = self.__universal_config.about_me.location.country
    country_span = self.__selenium_helper.get_element_by_exact_text(
      "Country",
      ElementType.SPAN,
      self.__context_element
    )
    country_select = self.__get_select_from_span(country_span)
    country_select.select_by_visible_text(country)

  def __is_willing_to_relocate_select(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Willing to Relocate",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_willing_to_relocate_select(self) -> None:
    assert self.__is_willing_to_relocate_select()
    willing_to_relocate = self.__universal_config.about_me.willing_to_relocate
    willing_to_relocate_span = self.__selenium_helper.get_element_by_exact_text(
      "Willing to Relocate",
      ElementType.SPAN,
      self.__context_element
    )
    willing_to_relocate_select = self.__get_select_from_span(willing_to_relocate_span)
    if willing_to_relocate:
      willing_to_relocate_select.select_by_value("Yes")
    else:
      willing_to_relocate_select.select_by_value("No")

  def __is_us_authorization_question_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Are you authorized to work in the USA?",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_us_authorization_question(self) -> None:
    assert self.__is_us_authorization_question_span()
    authorized = self.__universal_config.about_me.authorized_to_work_in_us
    relocation_span = self.__selenium_helper.get_element_by_exact_text(
      "Are you authorized to work in the USA?",
      ElementType.SPAN,
      self.__context_element
    )
    relocation_fieldset = relocation_span.find_element(By.XPATH, "../../..")
    if authorized:
      yes_label = relocation_fieldset.find_element(By.XPATH, "./div[1]/label")
      yes_label.click()
    else:
      no_label = relocation_fieldset.find_element(By.XPATH, "./div[2]/label")
      no_label.click()

  def __is_resume_selection_div(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Be sure to include an updated resume",
      ElementType.SPAN,
      self.__context_element
    )

  def __is_referral_span(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Were you referred by anyone to this position?",
      ElementType.SPAN,
      self.__context_element
    )

  def __handle_referral_question(self) -> None:
    assert self.__is_referral_span()
    referral_span = self.__selenium_helper.get_element_by_exact_text(
      "Were you referred by anyone to this position?",
      ElementType.SPAN,
      self.__context_element
    )
    referral_fieldset = referral_span.find_element(By.XPATH, "../../..")
    was_not_referred_label = self.__selenium_helper.get_element_by_exact_text(
      "No",
      ElementType.LABEL,
      referral_fieldset
    )
    was_not_referred_label.click()
    if self.__is_referral_followup_label():
      self.__handle_referral_followup_question()

  def __is_referral_followup_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "If Yes, who were you referred by and what is your relationship to them?",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_referral_followup_question(self) -> None:
    followup_label = self.__selenium_helper.get_element_by_exact_text(
      "If Yes, who were you referred by and what is your relationship to them?",
      ElementType.LABEL,
      self.__context_element
    )
    followup_input = self.__get_input_from_label(followup_label)
    self.__selenium_helper.write_to_input("N/A", followup_input)

  def __is_city_state_zip_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Address: City, State & Zip Code",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_city_state_zip(self) -> None:
    city = self.__universal_config.about_me.location.city
    state_code = self.__universal_config.about_me.location.state_code
    postal_code = self.__universal_config.about_me.location.postal_code
    city_state_zip = f"{city}, {state_code} {postal_code}"
    city_state_zip_label = self.__selenium_helper.get_element_by_exact_text(
      "Address: City, State & Zip Code",
      ElementType.LABEL,
      self.__context_element
    )
    city_state_zip_input = city_state_zip_label.find_element(By.XPATH, "../input")
    self.__selenium_helper.write_to_input(city_state_zip, city_state_zip_input)

  def __is_preferred_name_label(self) -> bool:
    return self.__selenium_helper.exact_text_is_present(
      "Preferred Name",
      ElementType.LABEL,
      self.__context_element
    )

  def __handle_preferred_name(self) -> None:
    assert self.__is_preferred_name_label()
    preferred_name = self.__universal_config.about_me.name.first
    preferred_name_label = self.__selenium_helper.get_element_by_exact_text(
      "Preferred Name",
      ElementType.LABEL,
      self.__context_element
    )
    preferred_name_input = preferred_name_label.find_element(By.XPATH, "../input")
    self.__selenium_helper.write_to_input(preferred_name, preferred_name_input)

  def __get_input_from_label(self, label: WebElement) -> WebElement:
    input_id = label.get_attribute("for")
    if input_id:
      input_el = self.__context_element.find_element(By.ID, input_id)
      return input_el
    raise NoSuchElementException("Invalid label_text.")

  def __get_select_from_span(self, span: WebElement) -> Select:
    label = span.find_element(By.XPATH, "..")
    select_id = label.get_attribute("for")
    if select_id:
      select = self.__context_element.find_element(By.ID, select_id)
      return Select(select)
    raise ValueError("Invalid span_text.")

  def __remove_suggestion_dialogs(self) -> None:
    self.__context_element.click()
