from fastapi import APIRouter

from app.api import (
    users,
    utils,
    hub,
    visit,
    vehicle,
    upload,
    route_optimization,
    tag,
    constraint,
)

api_router = APIRouter()

api_router.include_router(utils.router, tags=["utils"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(hub.router, tags=["hub"])
api_router.include_router(visit.router, tags=["visit"])
api_router.include_router(vehicle.router, tags=["vehicle"])
api_router.include_router(upload.router, tags=["uploads"])
api_router.include_router(route_optimization.router, tags=["route_optimization"])
api_router.include_router(tag.router, tags=["tag"])
api_router.include_router(constraint.router, tags=["constraint"])
