import sqlalchemy as sa
from sqlalchemy.dialects import (
    postgresql as postgresql_types,
)

try:
    from geoalchemy2 import types as geotypes
    from geoalchemy2.elements import WKBElement
    from geoalchemy2.shape import to_shape
except ImportError:
    pass
from sqlalchemy_serializer import SerializerMixin
from fastapi_users_db_sqlalchemy import GUID

from app.db import Base


class CustomSerializerMixin(SerializerMixin):
    serialize_types = ((WKBElement, lambda x: to_shape(x)),)


class Hub(Base, CustomSerializerMixin):
    __tablename__ = "vrp_hub"

    id = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    hubid = sa.Column(
        postgresql_types.VARCHAR(length=100),
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
    address = sa.Column(
        postgresql_types.VARCHAR(length=255),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    open = sa.Column(
        postgresql_types.TIME(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    close = sa.Column(
        postgresql_types.TIME(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    status = sa.Column(
        postgresql_types.VARCHAR(length=50),
        primary_key=False,
        unique=False,
        nullable=True,
    )
    geom = sa.Column(
        geotypes.Geometry(
            geometry_type="POINT", srid=4326, dimension=2, spatial_index=True
        ),
        primary_key=False,
        unique=False,
        nullable=True,
    )
    user_id = sa.Column(GUID, sa.ForeignKey("users.id"))

    visit = sa.orm.relationship(
        "Visit", back_populates="hub", cascade="all,delete", passive_deletes=True
    )
    vehicle = sa.orm.relationship(
        "Vehicle", back_populates="hub", cascade="all,delete", passive_deletes=True
    )
    constraint = sa.orm.relationship(
        "Constraint", back_populates="hub", cascade="all,delete", passive_deletes=True
    )
    vehicle_break = sa.orm.relationship(
        "VehicleBreak", back_populates="hub", cascade="all,delete", passive_deletes=True
    )
    tag = sa.orm.relationship(
        "Tag", back_populates="hub", cascade="all,delete", passive_deletes=True
    )
    tag_applies_to = sa.orm.relationship(
        "TagAppliesTo", back_populates="hub", cascade="all,delete", passive_deletes=True
    )
    tag = sa.orm.relationship(
        "Tag",
        back_populates="hub",
        cascade="all,delete",
        passive_deletes=True,
        order_by="Tag.id",
    )

    constraint = sa.orm.relationship(
        "Constraint",
        back_populates="hub",
        cascade="all,delete",
        passive_deletes=True,
        order_by="Constraint.id",
    )

    @property
    def serialize(self):
        return {
            "id": self.id,
            "hubid": self.hubid,
            "name": self.name,
            "address": self.address,
            "longitude": to_shape(self.geom).x,
            "latitude": to_shape(self.geom).y,
            "open": self.open,
            "close": self.close,
            "status": self.status,
        }

    @property
    def serialize_with_child(self):
        list_visit = []
        list_vehicle = []
        list_constraint = []
        list_tag = []
        if self.visit:
            for visit in self.visit:
                list_visit.append(
                    {
                        k: v if k != "geom" else v.__geo_interface__
                        for k, v in visit.serialize.items()
                    }
                )
        if self.vehicle:
            for vehicle in self.vehicle:
                list_vehicle.append(vehicle.serialize)
        if self.tag:
            for tag in self.tag:
                list_tag.append(tag.serialize)
        if self.constraint:
            for constraint in self.constraint:
                list_constraint.append(constraint.serialize)
        return {
            "id": self.id,
            "hubid": self.hubid,
            "name": self.name,
            "address": self.address,
            "open": self.open,
            "close": self.close,
            "status": self.status,
            "longitude": to_shape(self.geom).x,
            "latitude": to_shape(self.geom).y,
            "geom": to_shape(self.geom),
            "visites": list_visit,
            "vehicles": list_vehicle,
            "tags": list_tag,
            "constraints": list_constraint,
        }
