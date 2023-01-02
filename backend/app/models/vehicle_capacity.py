import sqlalchemy as sa
from sqlalchemy.dialects import (
    postgresql as postgresql_types,
)
from sqlalchemy.ext.hybrid import hybrid_property

try:
    from geoalchemy2 import types as geotypes
except ImportError:
    pass
from fastapi_users_db_sqlalchemy import GUID

from app.db import Base


class VehicleCapacity(Base):
    __tablename__ = "vrp_vehicle_capacity"

    id = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    constraint_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_constraint.id", ondelete="CASCADE"),
        index=True,
        primary_key=False,
        unique=False,
        nullable=False,
        autoincrement=True,
    )
    constraint = sa.orm.relationship(
        "Constraint",
        back_populates="vehicle_capacity",
        cascade="all,delete",
        passive_deletes=True,
        lazy="joined",
    )
    vehicle_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_vehicle.id", ondelete="CASCADE"),
        index=True,
        primary_key=False,
        unique=False,
        nullable=False,
        autoincrement=True,
    )
    value = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    user_id = sa.Column(GUID, sa.ForeignKey("users.id"))

    @hybrid_property
    def applies_id(self):
        return self.visit_id or self.vehicle_id

    @property
    def serialize(self):
        dict_constraint = {}
        if self.constraint:
            dict_constraint = self.constraint.serialize
        return {
            "id": dict_constraint["id"],
            "name": dict_constraint["name"],
            "unit": dict_constraint["unit"],
            "value": self.value,
        }
