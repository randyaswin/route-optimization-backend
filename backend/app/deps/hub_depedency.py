from app.models.constraint import Constraint
from app.models.tag import Tag


async def add_constraint(session, hub_id, user_id) -> None:
    default_constraint = [
        Constraint(hub_id=hub_id, name="weight", unit="kg", user_id=user_id),
        Constraint(hub_id=hub_id, name="volume", unit="m3", user_id=user_id),
    ]
    session.add_all(default_constraint)
    await session.commit()


async def add_tag(session, hub_id, user_id) -> None:
    default_tag = [Tag(hub_id=hub_id, name="default", user_id=user_id)]
    session.add_all(default_tag)
    await session.commit()
