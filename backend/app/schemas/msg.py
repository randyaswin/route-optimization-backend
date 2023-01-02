from typing import Optional
from pydantic import BaseModel


class Msg(BaseModel):
    msg: str


class Upload(Msg):
    total: int
    skiped: Optional[dict] = None
