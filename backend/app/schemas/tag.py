from typing import Optional
from pydantic import BaseModel
from datetime import time


class TagCreate(BaseModel):
    name: str
    hub_id: int


class TagUpdate(TagCreate):
    pass


class Tag(TagCreate):
    id: Optional[int]

    class Config:
        orm_mode = True
