from typing import Optional
from app.schemas.tag import Tag
from pydantic import BaseModel
from datetime import time


class VehicleBreak(BaseModel):
    name: str
    start: time
    end: time
    service_time: Optional[float] = 30


class VehicleCapacity(BaseModel):
    id: int
    value: int
    name: Optional[str]
    unit: Optional[str]


class VehicleUpdate(BaseModel):
    vehicleid: str
    name: str
    start: time
    end: time
    capacity: list[VehicleCapacity]
    profile: str
    active: Optional[bool] = True
    vehicle_break: Optional[list[VehicleBreak]] = []
    tag: Optional[list[Tag]] = []


class VehicleCreate(VehicleUpdate):
    hub_id: int


class Vehicle(VehicleCreate):
    id: int

    hub: Optional[dict] = None

    class Config:
        orm_mode = True
