"""add new constrain

Revision ID: cb4c161cefe4
Revises: 3edb04947198
Create Date: 2022-12-23 00:37:38.061612

"""
from alembic import op
import sqlalchemy as sa
import fastapi_users_db_sqlalchemy
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "cb4c161cefe4"
down_revision = "3edb04947198"
hub_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, "vrp_constraint", ["hub_id", "name"])
    op.create_unique_constraint(None, "vrp_constraint", ["id"])
    op.create_unique_constraint(None, "vrp_tag", ["id"])
    op.create_unique_constraint(None, "vrp_tag", ["hub_id", "name"])
    op.create_unique_constraint(None, "vrp_tag_applies_to", ["id"])
    op.create_unique_constraint(None, "vrp_vehicle_break", ["id"])
    op.create_unique_constraint(None, "vrp_vehicle_capacity", ["id"])
    op.create_unique_constraint(None, "vrp_visit_demand", ["id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "vrp_visit_demand", type_="unique")
    op.drop_constraint(None, "vrp_vehicle_capacity", type_="unique")
    op.drop_constraint(None, "vrp_vehicle_break", type_="unique")
    op.drop_constraint(None, "vrp_tag_applies_to", type_="unique")
    op.drop_constraint(None, "vrp_tag", type_="unique")
    op.drop_constraint(None, "vrp_tag", type_="unique")
    op.drop_constraint(None, "vrp_constraint", type_="unique")
    op.drop_constraint(None, "vrp_constraint", type_="unique")
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
    # ### end Alembic commands ###
