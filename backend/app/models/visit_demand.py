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


class VisitDemand(Base):
    __tablename__ = "vrp_visit_demand"

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
        back_populates="visit_demand",
        cascade="all,delete",
        passive_deletes=True,
    )
    visit_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_visit.id", ondelete="CASCADE"),
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
        return self.visit_id or self.visit_id

    @property
    def serialize(self):
        dict_constraint = {}
        if self.constraint:
            dict_constraint = self.constraint.serialize
        return {
            "id": self.id,
            "constraint_id": dict_constraint["id"],
            "name": dict_constraint["name"],
            "unit": dict_constraint["unit"],
            "value": self.value,
        }
