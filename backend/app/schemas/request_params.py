from typing import Any, Optional

from pydantic.main import BaseModel


class RequestParams(BaseModel):
    skip: int
    limit: int
    order_by: Any
    filter: Optional[Any] = None
