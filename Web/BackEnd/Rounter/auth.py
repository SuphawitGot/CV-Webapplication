from pydantic import BaseModel
from database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import Annotated
from model import User
from passlib.context import CryptContext 

SECRET_KEY = 'e5b81a4ba1f96761237b30889bb6c904aa9f3106638898dafd0a42a1dc95f627'
ALGORITHM = 'HS256'

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


router = APIRouter(
    prefix='/auth',
    tags=["auth"]
)
class createUserRequest(BaseModel):
    username: str
    email: str
    password: str
    licence_plate: str
    

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not pwd_context.verify(password, user.hash_password):
        return Falsea
    return user



db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request: createUserRequest, db: db_dependency):
    create_user_model = User(
        email=create_user_request.email,
        username=create_user_request.username,
        hash_password=pwd_context.hash(create_user_request.password),
        licence_plate=create_user_request.licence_plate
    )
    db.add(create_user_model)
    db.commit()


@router.post("/login")
async def login():
    return {"message": "Login successful"}  



@router.get("/all-users")
async def get_all_users(db: db_dependency):
    users = db.query(User).all()
    return users


