from abc import ABC, abstractmethod


class QueryUrlBuilder(ABC):
  @abstractmethod
  def build(self, search_term: str) -> str:
    pass
