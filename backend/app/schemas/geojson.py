from typing import Optional
from pydantic import BaseModel


class Geometry(BaseModel):
    type: str
    coordinates: list


class GeojsonFeature(BaseModel):
    type: str
    geometry: Geometry
    properties: dict

    class Config:
        orm_mode = True


class GeojsonFeatureCollection(BaseModel):
    type: str
    features: list[GeojsonFeature]

    class Config:
        orm_mode = True
