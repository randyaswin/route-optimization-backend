from typing import Any, List, Optional
from app.models.tag import Tag, TagAppliesTo
from app.models.visit_demand import VisitDemand

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import Response
from shapely.geometry import Point

from app.deps.db import get_async_session
from app.deps.request_params import parse_react_admin_params
from app.deps.serializer import serialize_geojson
from app.deps.users import current_user
from app.models.visit import Visit
from app.models.user import User
from app.schemas.visit import Visit as VisitSchema, VisitFeatureCollection
from app.schemas.visit import VisitCreate, VisitUpdate
from app.schemas.request_params import RequestParams

router = APIRouter(prefix="/visites")


@router.get("", response_model=List[VisitSchema])
async def get_visites(
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    request_params: RequestParams = Depends(parse_react_admin_params(Visit)),
    user: User = Depends(current_user),
) -> Any:
    total = await session.scalar(
        select(func.count(Visit.id).filter(Visit.user_id == user.id))
    )
    query = (
        select(Visit)
        .offset(request_params.skip)
        .limit(request_params.limit)
        .order_by(request_params.order_by)
        .filter(Visit.user_id == user.id)
    )

    query = query.filter(request_params.filter)
    query = query.options(selectinload(Visit.hub))
    query = query.options(selectinload(Visit.tag))
    query = query.options(selectinload(Visit.demand))
    visites = (await session.execute(query)).scalars().all()
    response.headers[
        "Content-Range"
    ] = f"{request_params.skip}-{request_params.skip + len(visites)}/{total}"
    return [visit.serialize for visit in visites]


@router.post("", status_code=201)
async def create_visit(
    visit_in: VisitCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    visit = Visit(
        visitid=visit_in["visitid"],
        name=visit_in["name"],
        hub_id=visit_in["hub_id"],
        address=visit_in["address"],
        open=visit_in["open"],
        close=visit_in["close"],
        service_time=visit_in["service_time"],
        geom=("SRID=4326;" + Point(visit_in["longitude"], visit_in["latitude"]).wkt),
        active=visit_in["active"],
        demand=[
            VisitDemand(constraint_id=demand.id, value=demand.value, user_id=user.id)
            for demand in visit_in.demand
        ],
    )
    visit.user_id = user.id
    for tag in visit_in.tag:
        t = (
            (
                await session.execute(
                    select(Tag).filter(
                        Tag.name == tag.name,
                        Tag.user_id == user.id,
                        Tag.hub_id == visit_in.hub_id,
                    )
                )
            )
            .scalars()
            .first()
        )
        if t is None:
            t = Tag(name=tag.name, user_id=user.id, hub_id=visit_in.hub_id)
        visit.tag.append(TagAppliesTo(tag=t, hub_id=visit_in.hub_id, user_id=user.id))
    session.add(visit)
    await session.commit()
    return {"id": visit.id}


@router.put("/{visit_id}")
async def update_visit(
    visit_id: int,
    visit_in: VisitUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    visit: Optional[Visit] = await session.get(Visit, visit_id)
    if not visit or visit.user_id != user.id:
        raise HTTPException(404)
    update_data = visit_in.dict(exclude_unset=True)
    update_data["geom"] = (
        "SRID=4326;" + Point(update_data["longitude"], update_data["latitude"]).wkt
    )
    update_data.pop("longitude")
    update_data.pop("latitude")
    for field, value in update_data.items():
        if field not in ["tag", "demand"]:
            setattr(visit, field, value)
    session.add(visit)
    await session.commit()
    if "tag" in update_data:
        query = (
            delete(TagAppliesTo)
            .filter(TagAppliesTo.visit_id == visit_id)
            .filter(TagAppliesTo.user_id == user.id)
        )
        await session.execute(query)
        tag = [
            TagAppliesTo(
                visit_id=visit_id, tag_id=tag, hub_id=visit.hub_id, user_id=user.id
            )
            for tag in visit_in.tag
        ]
        session.add_all(tag)
    if "demand" in update_data:
        query = (
            delete(VisitDemand)
            .filter(VisitDemand.visit_id == visit_id)
            .filter(VisitDemand.user_id == user.id)
        )
        await session.execute(query)
        demand = [
            VisitDemand(
                visit_id=visit_id,
                constraint_id=demand.id,
                value=demand.value,
                user_id=user.id,
            )
            for demand in visit_in.demand
        ]
        session.add_all(demand)
    await session.commit()
    return {"success": True}


@router.get("/{visit_id}", response_model=VisitSchema)
async def get_visit(
    visit_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    visit: Optional[Visit] = await session.get(Visit, visit_id)
    if not visit or visit.user_id != user.id:
        raise HTTPException(404)
    return visit.serialize


@router.get("/hub/{hub_id}", response_model=List[VisitSchema])
async def get_hub_visit(
    hub_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    visites: Optional[Visit] = (
        (
            await session.execute(
                select(Visit)
                .filter(Visit.hub_id == hub_id)
                .filter(Visit.user_id == user.id)
                .options(selectinload(Visit.hub))
                .options(selectinload(Visit.tag))
                .options(selectinload(Visit.demand))
            )
        )
        .scalars()
        .all()
    )
    if len(visites) == 0:
        raise HTTPException(404)
    return [
        serialize_geojson(visit.to_dict(), "geom", ["user_id"]) for visit in visites
    ]


@router.delete("/{visit_id}")
async def delete_visit(
    visit_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    visit: Optional[Visit] = await session.get(Visit, visit_id)
    if not visit or visit.user_id != user.id:
        raise HTTPException(404)
    await session.delete(visit)
    await session.commit()
    return {"success": True}
