from typing import Generic, TypeVar

from pydantic import BaseModel


DataType = TypeVar("DataType")


class PaginatedResponse(BaseModel, Generic[DataType]):
    items: list[DataType]
    total: int
    pagina: int
    limite: int
    total_paginas: int