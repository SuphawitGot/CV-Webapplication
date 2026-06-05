from Rounter import auth, detect
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from model import Base

app = FastAPI()
Base.metadata.create_all(bind=engine)  # ← creates tables automatically

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "FastAPI is running"}


app.include_router(auth.router)
app.include_router(detect.router)