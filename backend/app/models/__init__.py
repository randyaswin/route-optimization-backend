# Import all models here so alembic can discover them
from fastapi_users.db import SQLAlchemyBaseUserTable

from app.db import Base
from app.models.user import User
from app.models.hub import Hub
from app.models.visit import Visit
from app.models.vehicle import Vehicle
from app.models.constraint import Constraint
from app.models.visit_demand import VisitDemand
from app.models.vehicle_capacity import VehicleCapacity
from app.models.vehicle_break import VehicleBreak
from app.models.tag import Tag, TagAppliesTo
from app.models.optimized import Optimized
