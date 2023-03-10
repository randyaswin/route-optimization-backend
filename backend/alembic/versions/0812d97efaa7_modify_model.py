"""modify model

Revision ID: 0812d97efaa7
Revises: 
Create Date: 2022-12-22 15:04:03.159793

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import fastapi_users_db_sqlalchemy
import geoalchemy2

# revision identifiers, used by Alembic.
revision = "0812d97efaa7"
down_revision = None
hub_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "vrp_hub",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("hubid", sa.VARCHAR(length=100), nullable=True),
        sa.Column("name", sa.VARCHAR(length=50), nullable=False),
        sa.Column("address", sa.VARCHAR(length=255), nullable=False),
        sa.Column("open", postgresql.TIME(), nullable=False),
        sa.Column("close", postgresql.TIME(), nullable=False),
        sa.Column("status", sa.VARCHAR(length=50), nullable=True),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.Column(
            "user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "vrp_vehicle",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("vehicleid", sa.VARCHAR(length=100), nullable=True),
        sa.Column("name", sa.VARCHAR(length=50), nullable=False),
        sa.Column("profile", sa.VARCHAR(length=50), nullable=False),
        sa.Column("hub_id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("start", postgresql.TIME(), nullable=False),
        sa.Column("end", postgresql.TIME(), nullable=False),
        sa.Column("active", sa.BOOLEAN(), nullable=False),
        sa.Column(
            "user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True
        ),
        sa.ForeignKeyConstraint(["hub_id"], ["vrp_hub.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vrp_vehicle_id"), "vrp_vehicle", ["id"], unique=True)
    op.create_index(
        op.f("ix_vrp_vehicle_vehicleid"), "vrp_vehicle", ["vehicleid"], unique=False
    )
    op.create_table(
        "vrp_visit",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("visitid", sa.VARCHAR(length=100), nullable=True),
        sa.Column("name", sa.VARCHAR(length=50), nullable=False),
        sa.Column("hub_id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("address", sa.VARCHAR(length=255), nullable=False),
        sa.Column("open", postgresql.TIME(), nullable=False),
        sa.Column("close", postgresql.TIME(), nullable=False),
        sa.Column("service_time", sa.NUMERIC(precision=10, scale=1), nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=False,
        ),
        sa.Column("active", sa.BOOLEAN(), nullable=False),
        sa.Column(
            "user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True
        ),
        sa.ForeignKeyConstraint(["hub_id"], ["vrp_hub.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "vrp_data",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("hub_id", sa.INTEGER(), autoincrement=True, nullable=True),
        sa.Column("vehicle_id", sa.INTEGER(), autoincrement=True, nullable=True),
        sa.Column(
            "user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True
        ),
        sa.ForeignKeyConstraint(["hub_id"], ["vrp_hub.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vrp_vehicle.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "spatial_ref_sys",
        sa.Column("srid", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            "auth_name", sa.VARCHAR(length=256), autoincrement=False, nullable=True
        ),
        sa.Column("auth_srid", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "srtext", sa.VARCHAR(length=2048), autoincrement=False, nullable=True
        ),
        sa.Column(
            "proj4text", sa.VARCHAR(length=2048), autoincrement=False, nullable=True
        ),
        sa.CheckConstraint(
            "(srid > 0) AND (srid <= 998999)", name="spatial_ref_sys_srid_check"
        ),
        sa.PrimaryKeyConstraint("srid", name="spatial_ref_sys_pkey"),
    )
    op.drop_table("vrp_data")
    op.drop_table("vrp_visit")
    op.drop_index(op.f("ix_vrp_vehicle_vehicleid"), table_name="vrp_vehicle")
    op.drop_index(op.f("ix_vrp_vehicle_id"), table_name="vrp_vehicle")
    op.drop_table("vrp_vehicle")
    op.drop_table("vrp_hub")
    # ### end Alembic commands ###
