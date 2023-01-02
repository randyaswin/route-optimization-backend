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


class Visit(Base, CustomSerializerMixin):
    __tablename__ = "vrp_visit"

    id = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    visitid = sa.Column(
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
    hub_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_hub.id", ondelete="CASCADE"),
        primary_key=False,
        unique=False,
        nullable=False,
        autoincrement=True,
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
    demand = sa.orm.relationship(
        "VisitDemand",
        backref="vrp_visit",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    service_time = sa.Column(
        postgresql_types.NUMERIC(precision=10, scale=1),
        default=30,
        primary_key=False,
        unique=False,
        nullable=False,
    )
    tag = sa.orm.relationship(
        "TagAppliesTo",
        backref="visit",
        cascade="all,delete",
        passive_deletes=True,
    )
    geom = sa.Column(
        geotypes.Geometry(
            geometry_type="POINT", srid=4326, dimension=2, spatial_index=True
        ),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    active = sa.Column(
        postgresql_types.BOOLEAN(),
        default=True,
        primary_key=False,
        unique=False,
        nullable=False,
    )
    hub = sa.orm.relationship(
        "Hub", back_populates="visit", cascade="all,delete", passive_deletes=True
    )
    user_id = sa.Column(GUID, sa.ForeignKey("users.id"))

    @property
    def serialize(self):
        dict_hub = {}
        list_tag = []
        list_demand = []
        if self.hub:
            dict_hub = self.hub.serialize
        if self.tag:
            for tag in self.tag:
                list_tag.append(tag.serialize)
        if self.demand:
            for demand in self.demand:
                list_demand.append(demand.serialize)
        return {
            "id": self.id,
            "visitid": self.visitid,
            "name": self.name,
            "hub_id": self.hub_id,
            "address": self.address,
            "open": self.open,
            "close": self.close,
            "demand": list_demand,
            "service_time": self.service_time,
            "longitude": to_shape(self.geom).x,
            "latitude": to_shape(self.geom).y,
            "geom": to_shape(self.geom),
            "active": self.active,
            "tag": list_tag,
            "hub": {
                k: v if k != "geom" else v.__geo_interface__
                for k, v in dict_hub.items()
            },
        }
