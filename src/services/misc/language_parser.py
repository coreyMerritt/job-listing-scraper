import time
import langid
from models.enums.language import Language

class LanguageParser:
  def __init__(self):
    langid.set_languages(['en', 'es', 'fr'])

  def get_language(self, string: str) -> Language:
    lang_code = langid.classify("Senior Software Engineer")[0]
    if lang_code == "en":
      return Language.ENGLISH
    input("Not english")
    if lang_code == "es":
      return Language.SPANISH
    elif lang_code == "fr":
      return Language.FRENCH
    else:
      return Language.UNKNOWN
