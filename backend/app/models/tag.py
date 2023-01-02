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


class Tag(Base):
    __tablename__ = "vrp_tag"
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
    hub_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_hub.id", ondelete="CASCADE"),
        primary_key=False,
        unique=False,
        nullable=False,
        autoincrement=True,
    )
    hub = sa.orm.relationship(
        "Hub", back_populates="tag", cascade="all,delete", passive_deletes=True
    )
    tag_applies_to = sa.orm.relationship(
        "TagAppliesTo", back_populates="tag", cascade="all,delete", passive_deletes=True
    )
    user_id = sa.Column(GUID, sa.ForeignKey("users.id"))

    @property
    def serialize(self):
        return {"id": self.id, "hub_id": self.hub_id, "name": self.name}


class TagAppliesTo(Base):
    __tablename__ = "vrp_tag_applies_to"

    id = sa.Column(
        postgresql_types.INTEGER(),
        primary_key=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    tag_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_tag.id", ondelete="CASCADE"),
        index=True,
        primary_key=False,
        unique=False,
        nullable=False,
        autoincrement=True,
    )
    tag = sa.orm.relationship(
        "Tag",
        back_populates="tag_applies_to",
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
        nullable=True,
        autoincrement=True,
    )
    visit_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_visit.id", ondelete="CASCADE"),
        index=True,
        primary_key=False,
        unique=False,
        nullable=True,
        autoincrement=True,
    )
    hub_id = sa.Column(
        postgresql_types.INTEGER(),
        sa.ForeignKey(column="vrp_hub.id", ondelete="CASCADE"),
        index=True,
        primary_key=False,
        unique=False,
        nullable=False,
        autoincrement=True,
    )
    hub = sa.orm.relationship(
        "Hub",
        back_populates="tag_applies_to",
        cascade="all,delete",
        passive_deletes=True,
    )

    user_id = sa.Column(GUID, sa.ForeignKey("users.id"))

    @hybrid_property
    def applies_id(self):
        return self.visit_id or self.vehicle_id

    @property
    def serialize(self):
        dict_tag = {}
        if self.tag:
            dict_tag = self.tag.serialize
        return {
            "id": dict_tag["id"],
            "hub_id": dict_tag["hub_id"],
            "name": dict_tag["name"],
        }
