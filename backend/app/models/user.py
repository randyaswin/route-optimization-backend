from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import func

from app.db import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    firstname = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    # hub = relationship("Hub", back_populates="user", cascade="all, delete")
    # visit = relationship("Visit", back_populates="user", cascade="all, delete")
    # data = relationship("Data", back_populates="user", cascade="all, delete")
    # vehicle = relationship("Vehicle", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.email!r})"
