from typing import Optional
from pydantic import BaseModel
from app.schemas.tag import Tag
from datetime import time


class VisitDemand(BaseModel):
    id: int
    value: int
    name: Optional[str]
    unit: Optional[str]


class VisitUpdate(BaseModel):
    visitid: str
    name: str
    address: str
    open: time
    close: time
    demand: list[VisitDemand]
    service_time: float
    longitude: float
    latitude: float
    active: Optional[bool] = True
    tag: Optional[list[Tag]] = []


class VisitCreate(VisitUpdate):
    hub_id: int


class Visit(VisitCreate):
    id: int
    hub: Optional[dict] = None

    class Config:
        orm_mode = True


class Geometry(BaseModel):
    type: str
    coordinates: list


class VisitFeature(BaseModel):
    type: str
    geometry: Geometry
    properties: Visit

    class Config:
        orm_mode = True


class VisitFeatureCollection(BaseModel):
    type: str
    features: list[VisitFeature]

    class Config:
        orm_mode = True
