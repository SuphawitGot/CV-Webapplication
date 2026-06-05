from pydantic import BaseModel
from database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status # type: ignore
from sqlalchemy.orm import Session # type: ignore
from typing import Annotated
from model import User
from passlib.context import CryptContext 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


router = APIRouter(
    prefix='/auth',
    tags=["auth"]
)
class createUserRequest(BaseModel):
    username: str
    email: str
    role: str
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
        return False
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

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not pwd_context.verify(password, user.hash_password):
        return False
    return user



@router.get("/all-users")
async def get_all_users(db: db_dependency):
    users = db.query(User).all()
    return users


@router.get("/admin")
def admin_only(current_user = Depends(get_all_users)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    return {"message": "Welcome admin"}

