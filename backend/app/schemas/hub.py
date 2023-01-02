from typing import Optional
from pydantic import BaseModel
from datetime import time


class HubCreate(BaseModel):
    hubid: str
    name: str
    address: str
    open: time
    close: time
    status: Optional[str] = None
    longitude: float
    latitude: float


class HubUpdate(HubCreate):
    pass


class Hub(HubCreate):
    id: int
    visites: list[dict]
    vehicles: list[dict]
    tags: list[dict]
    constraints: list[dict]

    class Config:
        orm_mode = True


class HubNoChild(HubCreate):
    id: int

    class Config:
        orm_mode = True


class Geometry(BaseModel):
    type: str
    coordinates: list


class HubFeature(BaseModel):
    type: str
    geometry: Geometry
    properties: Hub

    class Config:
        orm_mode = True


class HubFeatureCollection(BaseModel):
    type: str
    features: list[HubFeature]

    class Config:
        orm_mode = True


class ListHub(BaseModel):
    id: int
    name: str
