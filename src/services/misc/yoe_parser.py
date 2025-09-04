import re


class YoeParser:
  __word_to_int = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20
  }

  __range_patterns = [
    r"(\d+)–(\d+) years",
    r"(\w+)–(\w+) years",
    r"(\d+) – (\d+) years",
    r"(\w+) – (\w+) years",
    r"(\d+)-(\d+) years",
    r"(\w+)-(\w+) years",
    r"(\d+) - (\d+) years",
    r"(\w+) - (\w+) years",
    r"(\d+) to (\d+) years",
    r"(\w+) to (\w+) years",
    r"(\d+)–(\d+)\+ years",
    r"(\w+)–(\w+)\+ years",
    r"(\d+) – (\d+)\+ years",
    r"(\w+) – (\w+)\+ years",
    r"(\d+)-(\d+)\+ years",
    r"(\w+)-(\w+)\+ years",
    r"(\d+) - (\d+)\+ years",
    r"(\w+) - (\w+)\+ years",
    r"(\d+) to (\d+)\+ years",
    r"(\w+) to (\w+)\+ years",
    r"(\d+)–(\d+) plus years",
    r"(\w+)–(\w+) plus years",
    r"(\d+) – (\d+) plus years",
    r"(\w+) – (\w+) plus years",
    r"(\d+)-(\d+) plus years",
    r"(\w+)-(\w+) plus years",
    r"(\d+) - (\d+) plus years",
    r"(\w+) - (\w+) plus years",
    r"(\d+) to (\d+) plus years",
    r"(\w+) to (\w+) plus years",
  ]

  __min_plus_patterns = [
    r"over (\d+) years",
    r"over (\w+) years",
    r"at least (\d+) years",
    r"at least (\w+) years",
    r"minimum of (\d+) years",
    r"minimum of (\w+) years",
    r"minimum (\d+) years",
    r"minimum (\w+) years",
    r"(\d+) plus years",
    r"(\w+) plus years",
    r"(\d+)\+ years",
    r"(\w+)\+ years",
    r"(\d+)\+years",
    r"(\w+)\+years",
  ]
  __min_only_patterns = [
    r"(\d+) years of experience",
    r"(\w+) years of experience",
    r"(\d+) years experience",
    r"(\w+) years experience",
    r"(\d+) years of professional",
    r"(\w+) years of professional",
    r"(\d+) years professional",
    r"(\w+) years professional",
    r"(\d+) years of progressive experience",
    r"(\w+) years of progressive experience",
  ]

  def parse(self, description: str) -> tuple[int | None, int | None]:
    description = description.lower()
    for pattern in self.__range_patterns:
      for match in re.finditer(pattern, description):
        matching_terms = match.groups()
        matching_nums: list[int] = []
        for term in matching_terms:
          if term.isdigit():
            matching_nums.append(int(term))
          elif term in self.__word_to_int:
            matching_nums.append(self.__word_to_int[term])
        if len(matching_nums) == 2:
          return matching_nums[0], matching_nums[1]
    for pattern in self.__min_plus_patterns + self.__min_only_patterns:
      for match in re.finditer(pattern, description):
        matching_terms = match.groups()
        matching_nums: list[int] = []
        for term in matching_terms:
          if term.isdigit():
            matching_nums.append(int(term))
          elif term in self.__word_to_int:
            matching_nums.append(self.__word_to_int[term])
        if len(matching_nums) != 0:
          return max(matching_nums), None
    return None, None
