from Rounter import auth
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from model import Base

app = FastAPI()
Base.metadata.create_all(bind=engine)  # ← creates tables automatically

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)