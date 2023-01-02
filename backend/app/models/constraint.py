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


class Constraint(Base):
    __tablename__ = "vrp_constraint"
    __table_args__ = (sa.UniqueConstraint("hub_id", "name"),)

    id = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    name = sa.Column(
        postgresql_types.VARCHAR(length=50),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    unit = sa.Column(
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

    hub = sa.orm.relationship(
        "Hub", back_populates="constraint", cascade="all,delete", passive_deletes=True
    )
    visit_demand = sa.orm.relationship(
        "VisitDemand",
        back_populates="constraint",
        cascade="all,delete",
        passive_deletes=True,
    )
    vehicle_capacity = sa.orm.relationship(
        "VehicleCapacity",
        back_populates="constraint",
        cascade="all,delete",
        passive_deletes=True,
    )
    user_id = sa.Column(GUID, sa.ForeignKey("users.id"))

    @property
    def serialize(self):
        return {"id": self.id, "name": self.name, "unit": self.unit}
