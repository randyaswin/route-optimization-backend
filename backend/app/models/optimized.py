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


class Optimized(Base):
    __tablename__ = "vrp_optimized"

    id = sa.Column(
        postgresql_types.UUID(), primary_key=True, unique=True, nullable=False
    )
    timestamp = sa.Column(
        postgresql_types.TIMESTAMP(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    cost = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    routes_count = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    unassigned_count = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    unassigned = sa.Column(
        postgresql_types.JSONB(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    routes = sa.Column(
        postgresql_types.JSONB(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    setup = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    service = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    duration = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    waiting_time = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    priority = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    loading = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    solving = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    delivery = sa.Column(
        postgresql_types.JSONB(),
        primary_key=False,
        unique=False,
        nullable=False,
    )
    amount = sa.Column(
        postgresql_types.JSONB(),
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
    user_id = sa.Column(GUID, sa.ForeignKey("users.id"))

    @property
    def serialize(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "cost": self.cost,
            "hub_id": self.hub_id,
            "routes_count": self.routes_count,
            "unassigned_count": self.routes_count,
            "setup": self.setup,
            "service": self.service,
            "duration": self.duration,
            "waiting_time": self.waiting_time,
            "priority": self.priority,
            "loading": self.loading,
            "solving": self.solving,
            "delivery": self.delivery,
            "amount": self.amount,
            "unassigned": self.unassigned,
            "routes": self.routes,
        }

    @property
    def serialize_simple(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "cost": self.cost,
            "hub_id": self.hub_id,
            "routes_count": self.routes_count,
            "unassigned_count": self.routes_count,
        }
