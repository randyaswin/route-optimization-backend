import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    firstname: str
    lastname: str
    email: str


class UserCreate(schemas.BaseUserCreate):
    firstname: str
    lastname: str
    email: str


class UserUpdate(schemas.BaseUserUpdate):
    firstname: str
    lastname: str
    email: str
