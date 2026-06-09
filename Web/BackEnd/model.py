from database import Base
from sqlalchemy import Column,  Integer, String, Boolean


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")
    hash_password = Column(String)
    licence_plate = Column(String, nullable=True)


class Violation(Base):
    __tablename__ = 'violations'
    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String, nullable=True)
    filename = Column(String)
    timestamp = Column(String)
   