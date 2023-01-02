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


class VehicleBreak(Base):
    __tablename__ = "vrp_vehicle_break"

    id = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    hub_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_hub.id", ondelete="CASCADE"),
        primary_key=False,
        unique=False,
        nullable=False,
        autoincrement=True,
    )
    name = sa.Column(
        postgresql_types.VARCHAR(length=50),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    vehicle_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_vehicle.id", ondelete="CASCADE"),
        primary_key=False,
        unique=False,
        nullable=True,
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
    service_time = sa.Column(
        postgresql_types.NUMERIC(precision=10, scale=1),
        primary_key=False,
        unique=False,
        nullable=True,
    )
    hub = sa.orm.relationship(
        "Hub",
        back_populates="vehicle_break",
        cascade="all,delete",
        passive_deletes=True,
    )
    vehicle = sa.orm.relationship(
        "Vehicle", back_populates="vehicle_break", passive_deletes=True
    )
    user_id = sa.Column(GUID, sa.ForeignKey("users.id"))
    # user = sa.orm.relationship("User", back_populates="vehicle")

    @property
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "service_time": self.service_time,
        }
