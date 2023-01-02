from typing import Any, List, Optional
from app.models.tag import Tag, TagAppliesTo
from app.models.vehicle_break import VehicleBreak
from app.models.vehicle_capacity import VehicleCapacity

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
from app.models.vehicle import Vehicle
from app.models.user import User
from app.schemas.vehicle import Vehicle as VehicleSchema
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.schemas.request_params import RequestParams

router = APIRouter(prefix="/vehicles")


@router.get("", response_model=List[VehicleSchema])
async def get_vehicles(
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    request_params: RequestParams = Depends(parse_react_admin_params(Vehicle)),
    user: User = Depends(current_user),
) -> Any:
    total = await session.scalar(
        select(func.count(Vehicle.id).filter(Vehicle.user_id == user.id))
    )
    vehicles = (
        (
            await session.execute(
                select(Vehicle)
                .offset(request_params.skip)
                .limit(request_params.limit)
                .order_by(request_params.order_by)
                .filter(Vehicle.user_id == user.id)
                .options(selectinload(Vehicle.hub))
                .options(selectinload(Vehicle.tag))
                .options(selectinload(Vehicle.capacity))
                .options(selectinload(Vehicle.vehicle_break))
            )
        )
        .scalars()
        .all()
    )
    response.headers[
        "Content-Range"
    ] = f"{request_params.skip}-{request_params.skip + len(vehicles)}/{total}"
    return [vehicle.serialize for vehicle in vehicles]


@router.post("", status_code=201)
async def create_vehicle(
    vehicle_in: VehicleCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    # vehicle_in = vehicle_in.dict()
    vehicle = Vehicle(
        vehicleid=vehicle_in.vehicleid,
        hub_id=vehicle_in.hub_id,
        name=vehicle_in.name,
        start=vehicle_in.start,
        end=vehicle_in.end,
        profile=vehicle_in.profile,
        active=vehicle_in.active,
        capacity=[
            VehicleCapacity(
                constraint_id=capacity.id, value=capacity.value, user_id=user.id
            )
            for capacity in vehicle_in.capacity
        ],
        vehicle_break=[
            VehicleBreak(
                hub_id=vehicle_in.hub_id,
                name=vehicle_break.name,
                start=vehicle_break.start,
                end=vehicle_break.end,
                service_time=vehicle_break.service_time,
                user_id=user.id,
            )
            for vehicle_break in vehicle_in.vehicle_break
        ],
    )
    vehicle.user_id = user.id
    for tag in vehicle_in.tag:
        t = (
            (
                await session.execute(
                    select(Tag).filter(
                        Tag.name == tag.name,
                        Tag.user_id == user.id,
                        Tag.hub_id == vehicle_in.hub_id,
                    )
                )
            )
            .scalars()
            .first()
        )
        if t is None:
            t = Tag(name=tag.name, user_id=user.id, hub_id=vehicle_in.hub_id)
        vehicle.tag.append(
            TagAppliesTo(tag=t, hub_id=vehicle_in.hub_id, user_id=user.id)
        )
    session.add(vehicle)
    await session.commit()
    return {"id": vehicle.id}


@router.put("/{vehicle_id}")
async def update_vehicle(
    vehicle_id: int,
    vehicle_in: VehicleUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    vehicle: Optional[Vehicle] = await session.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.user_id != user.id:
        raise HTTPException(404)
    update_data = vehicle_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field not in ["tag", "vehicle_break", "capacity"]:
            setattr(vehicle, field, value)
    session.add(vehicle)
    await session.commit()
    if "tag" in update_data:
        query = (
            delete(TagAppliesTo)
            .filter(TagAppliesTo.vehicle_id == vehicle_id)
            .filter(TagAppliesTo.user_id == user.id)
        )
        await session.execute(query)
        tag = [
            TagAppliesTo(
                vehicle_id=vehicle_id,
                tag_id=tag,
                hub_id=vehicle.hub_id,
                user_id=user.id,
            )
            for tag in vehicle_in.tag
        ]
        session.add_all(tag)
    if "vehicle_break" in update_data:
        query = (
            delete(VehicleBreak)
            .filter(VehicleBreak.vehicle_id == vehicle_id)
            .filter(VehicleBreak.user_id == user.id)
        )
        await session.execute(query)
        vehicle_break = [
            VehicleBreak(
                vehicle_id=vehicle_id,
                hub_id=vehicle.hub_id,
                name=vehicle_break.name,
                start=vehicle_break.start,
                end=vehicle_break.end,
                service_time=vehicle_break.service_time,
                user_id=user.id,
            )
            for vehicle_break in vehicle_in.vehicle_break
        ]
        session.add_all(vehicle_break)
    if "capacity" in update_data:
        query = (
            delete(VehicleCapacity)
            .filter(VehicleCapacity.vehicle_id == vehicle_id)
            .filter(VehicleCapacity.user_id == user.id)
        )
        await session.execute(query)
        capacity = [
            VehicleCapacity(
                vehicle_id=vehicle_id,
                constraint_id=capacity.id,
                value=capacity.value,
                user_id=user.id,
            )
            for capacity in vehicle_in.capacity
        ]
        session.add_all(capacity)
    await session.commit()
    return {"success": True}


@router.get("/{vehicle_id}", response_model=VehicleSchema)
async def get_vehicle(
    vehicle_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    vehicle: Optional[Vehicle] = await session.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.user_id != user.id:
        raise HTTPException(404)
    return vehicle


@router.get("/hub/{hub_id}", response_model=List[VehicleSchema])
async def get_hub_vehicle(
    hub_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    vehicle: Optional[Vehicle] = (
        (
            await session.execute(
                select(Vehicle)
                .filter(Vehicle.hub_id == hub_id)
                .filter(Vehicle.user_id == user.id)
                .options(selectinload(Vehicle.hub))
                .options(selectinload(Vehicle.tag))
                .options(selectinload(Vehicle.capacity))
                .options(selectinload(Vehicle.vehicle_break))
            )
        )
        .scalars()
        .all()
    )
    if len(vehicle) == 0:
        raise HTTPException(404)
    return vehicle


@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    vehicle: Optional[Vehicle] = await session.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.user_id != user.id:
        raise HTTPException(404)
    await session.delete(vehicle)
    await session.commit()
    return {"success": True}
