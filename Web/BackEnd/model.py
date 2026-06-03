from database import Base
from sqlalchemy import Column,  Integer, String, Boolean


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hash_password = Column(String)
    role = Column(String, default='user')
    licence_plate = Column(String, nullable=True)