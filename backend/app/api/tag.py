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
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import Tag as TagSchema
from app.schemas.tag import TagCreate, TagUpdate
from app.schemas.request_params import RequestParams

router = APIRouter(prefix="/tags")


@router.get("/hub/{hub_id}", response_model=List[TagSchema])
async def get_tags(
    hub_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    tag: Optional[Tag] = (
        (
            await session.execute(
                select(Tag).filter(Tag.hub_id == hub_id).filter(Tag.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    if len(tag) == 0:
        raise HTTPException(404)
    return tag


@router.post("", status_code=201)
async def create_tag(
    tag_in: TagCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    tag: Optional[Tag] = (
        (
            await session.execute(
                select(Tag)
                .filter(Tag.name == tag_in.name)
                .filter(Tag.hub_id == tag_in.hub_id)
                .filter(Tag.user_id == user.id)
            )
        )
        .scalars()
        .first()
    )
    if tag:
        return {"id": tag.id}
    tag_in = tag_in.dict()
    tag = Tag(**tag_in)
    tag.user_id = user.id
    session.add(tag)
    await session.commit()
    return {"id": tag.id}


@router.put("/{tag_id}")
async def update_tag(
    tag_id: int,
    tag_in: TagUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    tag: Optional[Tag] = await session.get(Tag, tag_id)
    if not tag or tag.user_id != user.id:
        raise HTTPException(404)
    update_data = tag_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)
    session.add(tag)
    await session.commit()
    return {"success": True}


@router.get("/{tag_id}", response_model=TagSchema)
async def get_tag(
    tag_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    tag: Optional[Tag] = await session.get(Tag, tag_id)
    if not tag or tag.user_id != user.id:
        raise HTTPException(404)
    return tag


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    tag: Optional[Tag] = await session.get(Tag, tag_id)
    if not tag or tag.user_id != user.id:
        raise HTTPException(404)
    await session.delete(tag)
    await session.commit()
    return {"success": True}
