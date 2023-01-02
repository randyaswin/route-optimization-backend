from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import Response
from shapely.geometry import Point

from app.deps.db import get_async_session
from app.deps.request_params import parse_react_admin_params
from app.deps.serializer import serialize_geojson
from app.deps.users import current_user
from app.models.constraint import Constraint
from app.models.user import User
from app.schemas.constraint import Constraint as ConstraintSchema
from app.schemas.constraint import ConstraintCreate, ConstraintUpdate
from app.schemas.request_params import RequestParams

router = APIRouter(prefix="/constraints")


@router.get("/hub/{hub_id}", response_model=List[ConstraintSchema])
async def get_constraints(
    hub_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    constraint: Optional[Constraint] = (
        (
            await session.execute(
                select(Constraint)
                .filter(Constraint.hub_id == hub_id)
                .filter(Constraint.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    if len(constraint) == 0:
        raise HTTPException(404)
    return constraint


@router.post("", status_code=201)
async def create_constraint(
    constraint_in: ConstraintCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    constraint: Optional[Constraint] = (
        (
            await session.execute(
                select(Constraint)
                .filter(Constraint.name == constraint_in.name)
                .filter(Constraint.hub_id == constraint_in.hub_id)
                .filter(Constraint.user_id == user.id)
            )
        )
        .scalars()
        .first()
    )
    if constraint:
        return {"id": constraint.id}
    constraint_in = constraint_in.dict()
    constraint = Constraint(**constraint_in)
    constraint.user_id = user.id
    session.add(constraint)
    await session.commit()
    return {"id": constraint.id}


@router.put("/{constraint_id}")
async def update_constraint(
    constraint_id: int,
    constraint_in: ConstraintUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    constraint: Optional[Constraint] = await session.get(Constraint, constraint_id)
    if not constraint or constraint.user_id != user.id:
        raise HTTPException(404)
    update_data = constraint_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(constraint, field, value)
    session.add(constraint)
    await session.commit()
    return {"success": True}


@router.get("/{constraint_id}", response_model=ConstraintSchema)
async def get_constraint(
    constraint_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    constraint: Optional[Constraint] = await session.get(Constraint, constraint_id)
    if not constraint or constraint.user_id != user.id:
        raise HTTPException(404)
    return constraint


@router.delete("/{constraint_id}")
async def delete_constraint(
    constraint_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    constraint: Optional[Constraint] = await session.get(Constraint, constraint_id)
    if not constraint or constraint.user_id != user.id:
        raise HTTPException(404)
    await session.delete(constraint)
    await session.commit()
    return {"success": True}
