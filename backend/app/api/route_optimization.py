from typing import Any, List, Optional
from uuid import UUID
from app.schemas.geojson import GeojsonFeatureCollection
from app.models.visit import Visit
from app.models.vehicle import Vehicle
from app.schemas.hub import Hub
from app.models.optimized import Optimized
from fastapi import APIRouter, Depends, Request, HTTPException
from starlette.responses import Response
from sqlalchemy import func, select, asc
from app.deps.request_params import parse_react_admin_params
import geopandas as gpd
import pandas as pd
import datetime
import httpx

from sqlalchemy import delete
from sqlalchemy.ext.asyncio.session import AsyncSession
from app.deps.db import get_async_session
from app.deps.users import current_user
from app.models.user import User
from app.schemas.request_params import RequestParams
from app.module.route_optimization import (
    route_optimization as route_optimization_module,
)

router = APIRouter(prefix="/route_optimization")


@router.post("", status_code=200)
async def route_optimization(
    data: Hub,
    user: User = Depends(current_user),
) -> Any:
    result = await route_optimization_module(data)
    return result


@router.get("/optimize", status_code=200)
async def solve(
    request: Request,
    response: Response,
    hub_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    async with httpx.AsyncClient() as client:
        hub = (
            await client.get(
                f"http://127.0.0.1:8003/api/v1/hubs/{hub_id}",
                headers={
                    "Authorization": request.headers["Authorization"],
                    "Content-type": "application/json",
                    "Accept": "application/json",
                    "Accept-Charset": "utf-8",
                },
            )
        ).json()

        response = await client.post(
            "http://127.0.0.1:8003/api/v1/route_optimization",
            json=hub,
            headers={
                "Authorization": request.headers["Authorization"],
                "Content-type": "application/json",
                "Accept": "application/json",
                "Accept-Charset": "utf-8",
            },
            timeout=None,
        )
        
    if response.status_code == 200:
        response = response.json()
        oprimized = Optimized(
            id = response['code'],
            timestamp = datetime.datetime.now(),
            cost = response['summary']['cost'],
            routes_count = response['summary']['routes'],
            unassigned_count = response['summary']['unassigned'],
            routes = response['routes'],
            unassigned = response['unassigned'],
            setup = response['summary']['setup'],
            service = response['summary']['service'],
            duration = response['summary']['duration'],
            waiting_time = response['summary']['waiting_time'],
            priority = response['summary']['priority'],
            loading = response['summary']['computing_times']['loading'],
            solving = response['summary']['computing_times']['solving'],
            delivery = response['summary']['delivery'],
            amount = response['summary']['amount'],
            hub_id = hub_id,
            user_id = user.id
        )
        session.add(oprimized)
        await session.commit()
        return response['code']
    else:
        return HTTPException(status_code=400, detail=response.text)
    
@router.get("/list", status_code=200)
async def list_optimized(
    response: Response,
    hub_id: int,
    session: AsyncSession = Depends(get_async_session),
    request_params: RequestParams = Depends(parse_react_admin_params(Optimized)),
    user: User = Depends(current_user),
) -> Any:
    total = await session.scalar(
        select(func.count(Optimized.id).filter(Optimized.user_id == user.id).filter(Optimized.hub_id == hub_id))
    )
    optimizeds = (
        (
            await session.execute(
                select(Optimized)
                .offset(request_params.skip)
                .limit(request_params.limit)
                .order_by(request_params.order_by)
                .filter(Optimized.user_id == user.id)
                .filter(Optimized.hub_id == hub_id)
            )
        )
        .scalars()
        .all()
    )
    response.headers[
        "Content-Range"
    ] = f"{request_params.skip}-{request_params.skip + len(optimizeds)}/{total}"
    return [optimized.serialize_simple for optimized in optimizeds]

@router.get("/{id}")
async def get_optimized(
    id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    optimized: Optional[Optimized] = (
        (
            await session.execute(
                select(Optimized)
                .filter(Optimized.id == id)
                .filter(Optimized.user_id == user.id)
            )
        )
        .scalars()
        .first()
    )
    if not optimized or optimized.user_id != user.id:
        raise HTTPException(404)
    return optimized.serialize