from typing import TypeVar, Generic, List
from pydantic import BaseModel, RootModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """ Модель для пагинированных ответов через API """
    page: int
    page_size: int
    count: int
    results: List[T]


class BoolResponse(RootModel[bool]):
    """ Модель для bool ответов через API """
    pass
