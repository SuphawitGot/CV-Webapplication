from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

is_running = False
is_paused  = False
app = FastAPI()

# ← Allow Next.js to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FastAPI is running"}

@app.post("/start")
def start():
    return {"status": "started"}

@app.post("/stop")
def stop():
    return {"status": "stopped"}
is_running = False
is_paused  = False

@app.post("/start")
def start():
    global is_running
    is_running = True
    return {"status": "started"}

@app.post("/stop")
def stop():
    global is_running
    is_running = False
    return {"status": "stopped"}

@app.post("/pause")
def pause():
    global is_paused
    is_paused = True
    return {"status": "paused"}

@app.post("/resume")
def resume():
    global is_paused
    is_paused = False
    return {"status": "resumed"}