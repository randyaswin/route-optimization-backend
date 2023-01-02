"""revice constrain

Revision ID: 52cede9053fa
Revises: cb4c161cefe4
Create Date: 2022-12-23 12:56:00.440519

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "52cede9053fa"
down_revision = "cb4c161cefe4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "vrp_tag_applies_to",
        "vehicle_id",
        existing_type=sa.INTEGER(),
        nullable=True,
        autoincrement=True,
    )
    op.alter_column(
        "vrp_tag_applies_to",
        "visit_id",
        existing_type=sa.INTEGER(),
        nullable=True,
        autoincrement=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "vrp_tag_applies_to",
        "visit_id",
        existing_type=sa.INTEGER(),
        nullable=False,
        autoincrement=True,
    )
    op.alter_column(
        "vrp_tag_applies_to",
        "vehicle_id",
        existing_type=sa.INTEGER(),
        nullable=False,
        autoincrement=True,
    )
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
