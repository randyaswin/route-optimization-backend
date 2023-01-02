from typing import Any, List, Optional
from app.deps.hub_depedency import add_constraint, add_tag
from app.models.vehicle import Vehicle
from app.models.visit import Visit
from app.models.constraint import Constraint
from app.models.tag import Tag

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, asc
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import Response
from sqlalchemy.orm import selectinload, load_only
from shapely.geometry import Point

from app.deps.db import get_async_session
from app.deps.request_params import parse_react_admin_params
from app.deps.serializer import serialize_geojson
from app.deps.users import current_user
from app.models.hub import Hub
from app.models.user import User
from app.schemas.hub import Hub as hubschema, HubNoChild, ListHub
from app.schemas.hub import HubCreate, HubUpdate
from app.schemas.request_params import RequestParams

router = APIRouter(prefix="/hubs")


@router.get("", response_model=List[HubNoChild])
async def get_hubs(
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    request_params: RequestParams = Depends(parse_react_admin_params(Hub)),
    user: User = Depends(current_user),
) -> Any:
    total = await session.scalar(
        select(func.count(Hub.id).filter(Hub.user_id == user.id))
    )
    hubs = (
        (
            await session.execute(
                select(Hub)
                .offset(request_params.skip)
                .limit(request_params.limit)
                .order_by(request_params.order_by)
                .filter(Hub.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    response.headers[
        "Content-Range"
    ] = f"{request_params.skip}-{request_params.skip + len(hubs)}/{total}"
    return [hub.serialize for hub in hubs]


@router.get("/list", response_model=List[ListHub])
async def get_list_hub(
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    request_params: RequestParams = Depends(parse_react_admin_params(Hub)),
    user: User = Depends(current_user),
) -> Any:
    hubs = (
        (
            await session.execute(
                select(Hub)
                .offset(request_params.skip)
                .limit(request_params.limit)
                .order_by(asc(Hub.__table__.c["name"]))
                .filter(Hub.user_id == user.id)
                .options(load_only("id", "name"))
            )
        )
        .scalars()
        .all()
    )
    return [{"id": hub.id, "name": hub.name} for hub in hubs]


@router.post("", status_code=201)
async def create_hub(
    hub_in: HubCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    hub_in = hub_in.dict()
    hub_in["geom"] = "SRID=4326;" + Point(hub_in["longitude"], hub_in["latitude"]).wkt
    hub_in.pop("longitude")
    hub_in.pop("latitude")
    hub = Hub(
        **hub_in,
        constraint=[
            Constraint(name="weight", unit="kg", user_id=user.id),
            Constraint(name="volume", unit="m3", user_id=user.id),
        ],
        tag=[Tag(name="default", user_id=user.id)],
    )
    hub.user_id = user.id
    session.add(hub)
    await session.commit()
    return {"id": hub.id}


@router.put("/{hub_id}")
async def update_hub(
    hub_id: int,
    hub_in: HubUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    hub: Optional[Hub] = await session.get(Hub, hub_id)
    if not hub or hub.user_id != user.id:
        raise HTTPException(404)
    update_data = hub_in.dict(exclude_unset=True)
    update_data["geom"] = (
        "SRID=4326;" + Point(update_data["longitude"], update_data["latitude"]).wkt
    )
    update_data.pop("longitude")
    update_data.pop("latitude")
    for field, value in update_data.items():
        setattr(hub, field, value)
    session.add(hub)
    await session.commit()
    return {"success": True}


@router.get("/{hub_id}", response_model=hubschema)
async def get_hub(
    hub_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    hub: Optional[Hub] = (
        (
            await session.execute(
                select(Hub)
                .filter(Hub.id == hub_id)
                .filter(Hub.user_id == user.id)
                .options(selectinload(Hub.visit))
                .options(selectinload(Hub.vehicle))
                .options(selectinload(Hub.tag))
                .options(selectinload(Hub.constraint))
                .options(selectinload(Hub.vehicle, Vehicle.tag))
                .options(selectinload(Hub.vehicle, Vehicle.capacity))
                .options(selectinload(Hub.vehicle, Vehicle.vehicle_break))
                .options(selectinload(Hub.visit, Visit.hub))
                .options(selectinload(Hub.visit, Visit.tag))
                .options(selectinload(Hub.visit, Visit.demand))
            )
        )
        .scalars()
        .first()
    )
    if not hub or hub.user_id != user.id:
        raise HTTPException(404)
    return hub.serialize_with_child


@router.delete("/{hub_id}")
async def delete_hub(
    hub_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    hub: Optional[Hub] = await session.get(Hub, hub_id)
    if not hub or hub.user_id != user.id:
        raise HTTPException(404)
    await session.delete(hub)
    await session.commit()
    return {"success": True}
