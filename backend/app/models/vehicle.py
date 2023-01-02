import sqlalchemy as sa
from sqlalchemy.dialects import (
    postgresql as postgresql_types,
)

try:
    from geoalchemy2 import types as geotypes
except ImportError:
    pass
from fastapi_users_db_sqlalchemy import GUID

from app.db import Base
from sqlalchemy_serializer import SerializerMixin


class Vehicle(Base, SerializerMixin):
    __tablename__ = "vrp_vehicle"

    id = sa.Column(
        postgresql_types.INTEGER(),
        index=True,
        primary_key=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    vehicleid = sa.Column(
        postgresql_types.VARCHAR(length=100),
        index=True,
        primary_key=False,
        unique=False,
        nullable=True,
    )
    name = sa.Column(
        postgresql_types.VARCHAR(length=50),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    profile = sa.Column(
        postgresql_types.VARCHAR(length=50),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    hub_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_hub.id", ondelete="CASCADE"),
        primary_key=False,
        unique=False,
        nullable=False,
        autoincrement=True,
    )
    start = sa.Column(
        postgresql_types.TIME(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    end = sa.Column(
        postgresql_types.TIME(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    capacity = sa.orm.relationship(
        "VehicleCapacity", backref="vehicle", cascade="all,delete", passive_deletes=True
    )
    active = sa.Column(
        postgresql_types.BOOLEAN(),
        default=True,
        primary_key=False,
        unique=False,
        nullable=False,
    )
    hub = sa.orm.relationship(
        "Hub", back_populates="vehicle", cascade="all,delete", passive_deletes=True
    )
    tag = sa.orm.relationship(
        "TagAppliesTo", backref="vehicle", cascade="all,delete", passive_deletes=True
    )
    vehicle_break = sa.orm.relationship(
        "VehicleBreak",
        back_populates="vehicle",
        cascade="all,delete",
        passive_deletes=True,
    )

    user_id = sa.Column(GUID, sa.ForeignKey("users.id"))

    @property
    def serialize(self):
        dict_hub = {}
        list_tag = []
        list_capacity = []
        list_break = []
        if self.hub:
            dict_hub = self.hub.serialize
        if self.tag:
            for tag in self.tag:
                list_tag.append(tag.serialize)
        if self.capacity:
            for capacity in self.capacity:
                list_capacity.append(capacity.serialize)
        if self.vehicle_break:
            for vehicle_break in self.vehicle_break:
                list_break.append(vehicle_break.serialize)
        return {
            "id": self.id,
            "vehicleid": self.vehicleid,
            "name": self.name,
            "profile": self.profile,
            "hub_id": self.hub_id,
            "start": self.start,
            "end": self.end,
            "capacity": list_capacity,
            "tag": list_tag,
            "active": self.active,
            "vehicle_break": list_break,
            "hub": {
                k: v if k != "geom" else v.__geo_interface__
                for k, v in dict_hub.items()
            },
        }

    @property
    def serialize_with_child(self):
        dict_hub = {}
        list_visit = []
        list_capacity = []
        if self.hub:
            dict_hub = self.hub.serialize
        if self.visit:
            for visit in self.visit:
                list_visit.append(
                    {
                        k: v if k != "geom" else v.__geo_interface__
                        for k, v in visit.serialize.items()
                    }
                )
        if self.capacity:
            for capacity in self.capacity:
                list_capacity.append(capacity.serialize)
        return {
            "id": self.id,
            "vehicleid": self.vehicleid,
            "name": self.name,
            "profile": self.profile,
            "hub_id": self.hub_id,
            "start": self.start,
            "end": self.end,
            "capacity": list_capacity,
            "active": self.active,
            "hub": {
                k: v if k != "geom" else v.__geo_interface__
                for k, v in dict_hub.items()
            },
            "visit": [
                {k: v if k != "geom" else v.__geo_interface__ for k, v in cust.items()}
                for cust in list_visit
            ],
        }
