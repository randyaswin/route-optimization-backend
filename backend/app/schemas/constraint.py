from typing import Optional
from pydantic import BaseModel
from datetime import time


class ConstraintCreate(BaseModel):
    name: str
    unit: str
    hub_id: int


class ConstraintUpdate(ConstraintCreate):
    pass


class Constraint(ConstraintCreate):
    id: Optional[int]

    class Config:
        orm_mode = True
