from typing import Any, List, Optional
from app.schemas.geojson import GeojsonFeatureCollection
from app.models.visit import Visit
from app.models.vehicle import Vehicle
from fastapi import APIRouter, Depends, Request, HTTPException
from starlette.responses import Response
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
from app.module.vrp import VrpOrtools

router = APIRouter(prefix="/vrp")


@router.post("", status_code=200)
async def vrp(
    hub: GeojsonFeatureCollection,
    visit: GeojsonFeatureCollection,
    vehicle: List[dict],
    workdays: Optional[List[str]] = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ],
    user: User = Depends(current_user),
) -> Any:
    route_json_hub = []
    point_json_hub = []
    input = {
        "hub": gpd.GeoDataFrame.from_features(hub.dict()),
        "vehicle": pd.DataFrame(vehicle),
        "visit": gpd.GeoDataFrame.from_features(visit.dict()),
        "start_date": None,
        "workdays": workdays,
        "timeuse": "weekly",
    }
    s = VrpOrtools()
    s.set_parameter(input)
    s.solving()
    point = s.make_points_all_new()
    route = s.make_route()
    return {
        "route": {"hub": int(input["hub"]["id"][0]), "route": route},
        "point": {
            "hub": int(input["hub"]["id"][0]),
            "point": point.astype(
                {
                    "id": "int",
                    "id_vehicle": "int",
                    "seq": "int",
                    "distance": "float",
                    "waktu": "float",
                }
            )
            .reset_index(drop=True)
            .__geo_interface__,
        },
    }


@router.get("/solve", status_code=200)
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
        visit = (
            await client.get(
                f"http://127.0.0.1:8003/api/v1/visites/hub/{hub_id}",
                headers={
                    "Authorization": request.headers["Authorization"],
                    "Content-type": "application/json",
                    "Accept": "application/json",
                    "Accept-Charset": "utf-8",
                },
            )
        ).json()
        vehicle = (
            await client.get(
                f"http://127.0.0.1:8003/api/v1/vehicles/hub/{hub_id}",
                headers={
                    "Authorization": request.headers["Authorization"],
                    "Content-type": "application/json",
                    "Accept": "application/json",
                    "Accept-Charset": "utf-8",
                },
            )
        ).json()
        payload = {
            "hub": hub,
            "visit": visit,
            "vehicle": vehicle,
            "workdays": [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ],
        }
        response = (
            await client.post(
                "http://127.0.0.1:8003/api/v1/vrp",
                json=payload,
                headers={
                    "Authorization": request.headers["Authorization"],
                    "Content-type": "application/json",
                    "Accept": "application/json",
                    "Accept-Charset": "utf-8",
                },
                timeout=None,
            )
        ).json()
        for k in response["point"]["point"]["features"]:
            visit: Optional[Visit] = await session.get(Visit, k["properties"]["id"])
            if not visit or visit.user_id != user.id or visit.hub_id != hub_id:
                continue
            update_data = dict(
                driving_distance=k["properties"]["distance"],
                driving_time=k["properties"]["waktu"],
                seq_sales=k["properties"]["seq"],
                vehicle_id=k["properties"]["id_vehicle"],
                datang=datetime.time(
                    *map(int, k["properties"]["datang"].split(".")[0].split(":"))
                ),
                berangkat=datetime.time(
                    *map(int, k["properties"]["berangkat"].split(".")[0].split(":"))
                ),
            )
            for field, value in update_data.items():
                setattr(visit, field, value)
            session.add(visit)
            await session.commit()
        for k in response["route"]["route"]:
            vehicle: Optional[Vehicle] = await session.get(Vehicle, k["vehicle_id"])
            if not vehicle or vehicle.user_id != user.id or vehicle.hub_id != hub_id:
                continue
            update_data = dict(
                total_distance=k["total_distance"],
                total_time=k["total_time"],
                total_load=k["total_load"],
            )
            for field, value in update_data.items():
                setattr(vehicle, field, value)
            session.add(vehicle)
            # await session.execute(delete(Data).where(Data.user_id == user.id).where(Data.hub_id == hub_id))
            # for d in k["route_data"]['features']:
            #     data = Data(hub_id=hub_id,
            #                 vehicle_id=d["properties"]["id_vehicle"],
            #                 data=d
            #                 )
            #     data.user_id = user.id
            #     session.add(data)
            await session.commit()
    return {"message": "solved"}
