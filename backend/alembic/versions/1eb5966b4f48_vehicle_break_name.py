"""vehicle break name

Revision ID: 1eb5966b4f48
Revises: 52cede9053fa
Create Date: 2022-12-24 04:01:12.507219

"""
from alembic import op
import sqlalchemy as sa
import fastapi_users_db_sqlalchemy
import geoalchemy2

# revision identifiers, used by Alembic.
revision = "1eb5966b4f48"
down_revision = "52cede9053fa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "vrp_vehicle_break", sa.Column("name", sa.VARCHAR(length=50), nullable=False)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("vrp_vehicle_break", "name")
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
