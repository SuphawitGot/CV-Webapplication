from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from ML.Detector import gg

is_running = False
is_paused  = False
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
