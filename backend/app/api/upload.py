from typing import Any, List, Optional
import os
import datetime
import pandas as pd
import numpy as np
from app.schemas.msg import Msg, Upload
from app.models.visit import Visit
from app.models.constraint import Constraint
from app.models.tag import Tag, TagAppliesTo
from app.deps.time_parser import parse_time
from app.models.vehicle_break import VehicleBreak
from app.models.vehicle_capacity import VehicleCapacity
from app.models.visit_demand import VisitDemand
from fastapi import APIRouter, Depends, HTTPException
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File, Body
from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import Response
from shapely.geometry import Point
from collections import defaultdict

from app.deps.db import get_async_session
from app.deps.request_params import parse_react_admin_params
from app.deps.serializer import serialize_geojson
from app.deps.users import current_user
from app.models.hub import Hub
from app.models.vehicle import Vehicle
from app.models.user import User
from app.schemas.hub import Hub as hubschema, HubFeatureCollection
from app.schemas.hub import HubCreate, HubUpdate
from app.schemas.request_params import RequestParams

router = APIRouter(prefix="/upload")


@router.post(
    "/hub", status_code=201, responses={400: {"model": Msg}, 201: {"model": Msg}}
)
async def upload_hub(
    response: Response,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    filename = file.filename
    split_file_name = os.path.splitext(
        filename
    )  # split the file name into two different path (string + extention)
    file_extension = split_file_name[1]  # file extention
    if file_extension == ".csv":
        data = pd.read_csv(file.file._file).reset_index(drop=True)
        hubs = []
        total_added = 0
        for idx, row in data.iterrows():
            hubs.append(
                Hub(
                    hubid=str(row["hubID"]),
                    name=str(row["name"]),
                    address=str(row["address"]),
                    open=parse_time(row["open"]),
                    close=parse_time(row["close"]),
                    geom="SRID=4326;" + Point(row["longitude"], row["latitude"]).wkt,
                    user_id=user.id,
                    constraint=[
                        Constraint(name="weight", unit="kg", user_id=user.id),
                        Constraint(name="volume", unit="m3", user_id=user.id),
                    ],
                    tag=[Tag(name="default", user_id=user.id)],
                )
            )
            total_added = total_added + 1
        session.add_all(hubs)
        await session.commit()
        return {"message": "Upload file successfully", "total": total_added}
    else:
        response.status_code = 400
        return {"message": "File extension is not csv"}


@router.post(
    "/hub/{hub_id}/visit",
    status_code=201,
    responses={400: {"model": Msg}, 201: {"model": Upload}},
)
async def upload_hub_visit(
    response: Response,
    hub_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    filename = file.filename
    split_file_name = os.path.splitext(
        filename
    )  # split the file name into two different path (string + extention)
    file_extension = split_file_name[1]  # file extention
    if file_extension == ".csv":
        data = pd.read_csv(file.file._file).reset_index(drop=True)
        demand_label = [
            {"name": s.split(":")[1], "unit": s.split(":")[2], "column": s}
            for s in data.columns
            if s.startswith("demand")
        ]
        visites = []
        no_hub = 0
        total_added = 0
        demand = []
        for s in demand_label:
            t = (
                (
                    await session.execute(
                        select(Constraint).filter(
                            Constraint.name == s["name"],
                            Constraint.unit == s["unit"],
                            Constraint.user_id == user.id,
                            Constraint.hub_id == hub_id,
                        )
                    )
                )
                .scalars()
                .first()
            )
            if t is None:
                t = Constraint(
                    name=s["name"], unit=s["unit"], user_id=user.id, hub_id=hub_id
                )
            demand.append({"column": s["column"], "constraint": t})
        tags = {}
        tag_set = set(
            [
                j
                for sub in [
                    i.strip().split(",") for i in data.tag.unique() if i is not np.nan
                ]
                for j in sub
            ]
        )
        for tag in tag_set:
            t = (
                (
                    await session.execute(
                        select(Tag).filter(
                            Tag.name == tag,
                            Tag.user_id == user.id,
                            Tag.hub_id == hub_id,
                        )
                    )
                )
                .scalars()
                .first()
            )
            if t is None:
                t = Tag(name=tag, user_id=user.id, hub_id=hub_id)
            tags[tag] = t
        for idx, row in data.iterrows():
            visit = Visit(
                visitid=str(row["visitID"]),
                name=row["name"],
                hub_id=hub_id,
                service_time=row["service_time"],
                address=row["address"],
                open=parse_time(row["open"]),
                close=parse_time(row["close"]),
                geom="SRID=4326;" + Point(row["longitude"], row["latitude"]).wkt,
                user_id=user.id,
            )
            visit.demand = [
                VisitDemand(
                    constraint=item["constraint"],
                    value=row[item["column"]],
                    user_id=user.id,
                )
                for item in demand
                if row[item["column"]] is not None
            ]
            if row["tag"] is not np.nan:
                visit.tag = [
                    TagAppliesTo(tag=tags[tag], hub_id=hub_id, user_id=user.id)
                    for tag in row["tag"].strip().split(",")
                ]
            visites.append(visit)
            total_added += 1
        session.add_all(visites)
        await session.commit()
        return {
            "message": "Upload file successfully",
            "total": total_added,
            "skiped": {"no_hub": no_hub},
        }
    else:
        response.status_code = 400
        return {"message": "File extension is not csv"}


@router.post(
    "/hub/{hub_id}/vehicle",
    status_code=201,
    responses={400: {"model": Msg}, 201: {"model": Upload}},
)
async def upload_hub_vehicle(
    response: Response,
    hub_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    filename = file.filename
    split_file_name = os.path.splitext(
        filename
    )  # split the file name into two different path (string + extention)
    file_extension = split_file_name[1]  # file extention
    if file_extension == ".csv":
        data = pd.read_csv(file.file._file).reset_index(drop=True)
        capacity_label = [
            {"name": s.split(":")[1], "unit": s.split(":")[2], "column": s}
            for s in data.columns
            if s.startswith("capacity")
        ]

        breaks_label = [s for s in data.columns if s.startswith("break")]
        d = defaultdict(list)
        b = []
        for item in breaks_label:
            i = item.split(":")
            d[i[1]].append({i[2]: item})
        breaks_label = [
            {k: v for list_item in d[idx] for (k, v) in list_item.items()}
            for idx, _ in d.items()
        ]
        vehicles = []
        no_hub = 0
        total_added = 0
        capacity = []
        for s in capacity_label:
            t = (
                (
                    await session.execute(
                        select(Constraint).filter(
                            Constraint.name == s["name"],
                            Constraint.unit == s["unit"],
                            Constraint.user_id == user.id,
                            Constraint.hub_id == hub_id,
                        )
                    )
                )
                .scalars()
                .first()
            )
            if t is None:
                t = Constraint(
                    name=s["name"], unit=s["unit"], user_id=user.id, hub_id=hub_id
                )
            capacity.append({"column": s["column"], "constraint": t})
        tags = {}
        tag_set = set(
            [
                j
                for sub in [i.split(",") for i in data.tag.unique() if i is not np.nan]
                for j in sub
            ]
        )
        for tag in tag_set:
            t = (
                (
                    await session.execute(
                        select(Tag).filter(
                            Tag.name == tag,
                            Tag.user_id == user.id,
                            Tag.hub_id == hub_id,
                        )
                    )
                )
                .scalars()
                .first()
            )
            if t is None:
                t = Tag(name=tag, user_id=user.id, hub_id=hub_id)
            tags[tag] = t

        for idx, row in data.iterrows():
            vehicle = Vehicle(
                vehicleid=str(row["vehicleID"]),
                name=row["name"],
                hub_id=hub_id,
                start=parse_time(row["start"]),
                end=parse_time(row["end"]),
                profile=row["profile"],
                user_id=user.id,
            )
            vehicle.vehicle_break = [
                VehicleBreak(
                    name=row[item["name"]],
                    start=parse_time(row[item["start"]]),
                    end=parse_time(row[item["end"]]),
                    service_time=row[item["service_time"]],
                    hub_id=hub_id,
                    user_id=user.id,
                )
                for item in breaks_label
            ]
            vehicle.capacity = [
                VehicleCapacity(
                    constraint=item["constraint"],
                    value=row[item["column"]],
                    user_id=user.id,
                )
                for item in capacity
                if row[item["column"]] is not None
            ]
            if row["tag"] is not np.nan:
                vehicle.tag = [
                    TagAppliesTo(tag=tags[tag], hub_id=hub_id, user_id=user.id)
                    for tag in row["tag"].strip().split(",")
                    if tag is not None
                ]
            vehicles.append(vehicle)
            total_added += 1
        session.add_all(vehicles)
        await session.commit()
        return {
            "message": "Upload file successfully",
            "total": total_added,
            "skiped": {"no_hub": no_hub},
        }
    else:
        response.status_code = 400
        return {"message": "File extension is not csv"}


@router.post(
    "/visit",
    status_code=201,
    responses={400: {"model": Msg}, 201: {"model": Upload}},
)
async def upload_visit(
    response: Response,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    filename = file.filename
    split_file_name = os.path.splitext(
        filename
    )  # split the file name into two different path (string + extention)
    file_extension = split_file_name[1]  # file extention
    if file_extension == ".csv":
        data = pd.read_csv(file.file._file).reset_index(drop=True)
        demand_label = [
            {"name": s.split(":")[1], "unit": s.split(":")[2], "column": s}
            for s in data.columns
            if s.startswith("demand")
        ]
        visites = []
        no_hub = 0
        total_added = 0
        data = data.groupby("hubID")
        for group, data_group in data:
            hub = (
                (
                    await session.execute(
                        select(Hub)
                        .filter(Hub.user_id == user.id)
                        .filter(Hub.hubid == str(group))
                    )
                )
                .scalars()
                .first()
            )
            demand = []
            for s in demand_label:
                t = (
                    (
                        await session.execute(
                            select(Constraint).filter(
                                Constraint.name == s["name"],
                                Constraint.unit == s["unit"],
                                Constraint.user_id == user.id,
                                Constraint.hub_id == hub.id,
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if t is None:
                    t = Constraint(
                        name=s["name"], unit=s["unit"], user_id=user.id, hub_id=hub.id
                    )
                demand.append({"column": s["column"], "constraint": t})
            tags = {}
            tag_set = set(
                [
                    j
                    for sub in [
                        i.strip().split(",")
                        for i in data_group.tag.unique()
                        if i is not np.nan
                    ]
                    for j in sub
                ]
            )
            for tag in tag_set:
                t = (
                    (
                        await session.execute(
                            select(Tag).filter(
                                Tag.name == tag,
                                Tag.user_id == user.id,
                                Tag.hub_id == hub.id,
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if t is None:
                    t = Tag(name=tag, user_id=user.id, hub_id=hub.id)
                tags[tag] = t
            for idx, row in data_group.iterrows():
                if hub:

                    visit = Visit(
                        visitid=str(row["visitID"]),
                        name=row["name"],
                        hub_id=hub.id,
                        service_time=row["service_time"],
                        address=row["address"],
                        open=parse_time(row["open"]),
                        close=parse_time(row["close"]),
                        geom="SRID=4326;"
                        + Point(row["longitude"], row["latitude"]).wkt,
                        user_id=user.id,
                    )
                    visit.demand = [
                        VisitDemand(
                            constraint=item["constraint"],
                            value=row[item["column"]],
                            user_id=user.id,
                        )
                        for item in demand
                        if row[item["column"]] is not None
                    ]
                    if row["tag"] is not np.nan:
                        visit.tag = [
                            TagAppliesTo(tag=tags[tag], hub_id=hub.id, user_id=user.id)
                            for tag in row["tag"].strip().split(",")
                        ]
                    visites.append(visit)
                    total_added += 1
                else:
                    no_hub += 1
        session.add_all(visites)
        await session.commit()
        return {
            "message": "Upload file successfully",
            "total": total_added,
            "skiped": {"no_hub": no_hub},
        }
    else:
        response.status_code = 400
        return {"message": "File extension is not csv"}


@router.post(
    "/vehicle", status_code=201, responses={400: {"model": Msg}, 201: {"model": Upload}}
)
async def upload_vehicle(
    response: Response,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
) -> Any:
    filename = file.filename
    split_file_name = os.path.splitext(
        filename
    )  # split the file name into two different path (string + extention)
    file_extension = split_file_name[1]  # file extention
    if file_extension == ".csv":
        data = pd.read_csv(file.file._file).reset_index(drop=True)
        capacity_label = [
            {"name": s.split(":")[1], "unit": s.split(":")[2], "column": s}
            for s in data.columns
            if s.startswith("capacity")
        ]

        breaks_label = [s for s in data.columns if s.startswith("break")]
        d = defaultdict(list)
        b = []
        for item in breaks_label:
            i = item.split(":")
            d[i[1]].append({i[2]: item})
        breaks_label = [
            {k: v for list_item in d[idx] for (k, v) in list_item.items()}
            for idx, _ in d.items()
        ]
        vehicles = []
        no_hub = 0
        total_added = 0
        data = data.groupby("hubID")
        for group, data_group in data:
            hub = (
                (
                    await session.execute(
                        select(Hub)
                        .filter(Hub.user_id == user.id)
                        .filter(Hub.hubid == str(group))
                    )
                )
                .scalars()
                .first()
            )
            capacity = []
            for s in capacity_label:
                t = (
                    (
                        await session.execute(
                            select(Constraint).filter(
                                Constraint.name == s["name"],
                                Constraint.unit == s["unit"],
                                Constraint.user_id == user.id,
                                Constraint.hub_id == hub.id,
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if t is None:
                    t = Constraint(
                        name=s["name"], unit=s["unit"], user_id=user.id, hub_id=hub.id
                    )
                capacity.append({"column": s["column"], "constraint": t})
            tags = {}
            tag_set = set(
                [
                    j
                    for sub in [
                        i.split(",") for i in data_group.tag.unique() if i is not np.nan
                    ]
                    for j in sub
                ]
            )
            for tag in tag_set:
                t = (
                    (
                        await session.execute(
                            select(Tag).filter(
                                Tag.name == tag,
                                Tag.user_id == user.id,
                                Tag.hub_id == hub.id,
                            )
                        )
                    )
                    .scalars()
                    .first()
                )
                if t is None:
                    t = Tag(name=tag, user_id=user.id, hub_id=hub.id)
                tags[tag] = t

            for idx, row in data_group.iterrows():
                if hub:

                    vehicle = Vehicle(
                        vehicleid=str(row["vehicleID"]),
                        name=row["name"],
                        hub=hub,
                        start=parse_time(row["start"]),
                        end=parse_time(row["end"]),
                        profile=row["profile"],
                        user_id=user.id,
                    )
                    vehicle.vehicle_break = [
                        VehicleBreak(
                            name=row[item["name"]],
                            start=parse_time(row[item["start"]]),
                            end=parse_time(row[item["end"]]),
                            service_time=row[item["service_time"]],
                            hub_id=hub.id,
                            user_id=user.id,
                        )
                        for item in breaks_label
                    ]
                    vehicle.capacity = [
                        VehicleCapacity(
                            constraint=item["constraint"],
                            value=row[item["column"]],
                            user_id=user.id,
                        )
                        for item in capacity
                        if row[item["column"]] is not None
                    ]
                    if row["tag"] is not np.nan:
                        vehicle.tag = [
                            TagAppliesTo(tag=tags[tag], hub_id=hub.id, user_id=user.id)
                            for tag in row["tag"].strip().split(",")
                            if tag is not None
                        ]
                    vehicles.append(vehicle)
                    total_added += 1
                else:
                    no_hub += 1
        session.add_all(vehicles)
        await session.commit()
        return {
            "message": "Upload file successfully",
            "total": total_added,
            "skiped": {"no_hub": no_hub},
        }
    else:
        response.status_code = 400
        return {"message": "File extension is not csv"}


@router.get(
    "/destroy", status_code=200, responses={400: {"model": Msg}, 200: {"model": Msg}}
)  # delete all data
async def destroy(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
) -> Any:
    await session.execute(delete(Visit).where(Visit.user_id == user.id))
    await session.execute(delete(Vehicle).where(Vehicle.user_id == user.id))
    await session.execute(delete(Hub).where(Hub.user_id == user.id))
    await session.commit()
    return {"message": "Delete all data successfully"}
