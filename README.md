# CV-Webapplication

### AI-Assisted Zebra Crossing Monitoring

A full-stack computer vision prototype for detecting cars and motorcycles occupying zebra crossings in uploaded videos. The application combines YOLO object detection, license plate recognition, and a web dashboard to display annotated video and automatically capture potential violations.

Developed by **Suphawit Sudsang**, Computer Engineering, Rangsit University.

## Features

- **Video upload:** Drag and drop a video or select a file to start detection.
- **Annotated video stream:** Display vehicle, crosswalk, and license plate bounding boxes through an MJPEG stream.
- **Automatic captures:** Save a frame when a vehicle's bottom-center point enters a detected crosswalk region, subject to a three-second global cooldown.
- **License plate recognition:** Detect plate regions and use EasyOCR with Thai and English language support.
- **Detection controls:** Pause, resume, and stop processing from the dashboard.
- **Capture feed:** Show timestamps and asynchronously recognized plate text, refreshed every 1.5 seconds while detection runs.
- **Database integration:** Define PostgreSQL tables for users and violation records, with violation writes performed by the OCR worker.
- **User page prototype:** Search sample license plate records at `/user`.

> **Project status:** This is a development prototype. Detection flags crosswalk occupancy; it does not currently measure how long a vehicle has stopped or determine whether an actual traffic violation occurred. The user search page uses mock data, and authentication is incomplete.

## Technology Stack

| Layer | Technologies |
| --- | --- |
| Frontend | Next.js 16.2.6, React 19.2.4, TypeScript, Tailwind CSS 4 |
| Backend | Python 3.13+, FastAPI, Uvicorn |
| Computer vision | Ultralytics YOLO, OpenCV, PyTorch, ByteTrack configuration |
| OCR | EasyOCR with Thai and English support |
| Database | PostgreSQL 16, SQLAlchemy, psycopg2 |
| Tooling | uv, npm, Docker, Docker Compose |

## How It Works

1. The frontend uploads a video to the FastAPI backend.
2. A reader thread loads frames and loops the video when it reaches the end.
3. A detection thread processes frames at half resolution using separate vehicle, crosswalk, and plate models.
4. The detector checks whether each vehicle's bottom-center point lies inside a crosswalk bounding box.
5. When the cooldown permits, it saves an annotated frame and starts background OCR on the plate crop, or the vehicle crop as a fallback.
6. OCR updates the session's capture record and attempts to store the result in PostgreSQL.
7. The browser displays annotated frames and polls the session's capture list.

## Repository Structure

```text
CV-Webapplication/
├── docker-compose.yml
├── README.md
├── yolo26n.pt
├── yolov8n.pt
└── Web/
    ├── BackEnd/
    │   ├── main.py                 # FastAPI application and static files
    │   ├── database.py             # Database connection and sessions
    │   ├── model.py                # User and Violation tables
    │   ├── pyproject.toml          # Python dependencies
    │   ├── Dockerfile
    │   ├── yolo26n.pt              # Vehicle model used by the backend
    │   ├── Rounter/                # Directory name as committed
    │   │   ├── auth.py             # User-related endpoints
    │   │   └── detect.py           # Upload, stream, and processing controls
    │   ├── ML/
    │   │   ├── Detector.py         # Detection, capture, and OCR pipeline
    │   │   └── Train_model/
    │   │       └── licence_plate_model.py
    │   └── uploads/
    └── frontend/
        ├── app/
        │   ├── page.tsx            # Detection dashboard
        │   └── user/page.tsx       # Search page with sample data
        ├── public/
        ├── package.json
        ├── next.config.ts
        └── dockerfile
```

## Required Model Files

The backend loads these files when detection starts:

| File | Purpose | Included in repository |
| --- | --- | --- |
| `Web/BackEnd/yolo26n.pt` | Car and motorcycle detection | Yes |
| `Web/BackEnd/ML/best.pt` | Crosswalk detection | No |
| `Web/BackEnd/ML/LC.pt` | License plate detection | No |

**Provide the two missing trained model files at these exact paths before uploading a video.** The repository does not provide download links for them.

The plate training script references a local Windows dataset path. To use it, supply your own compatible dataset and update the `data` path. Its `name="LC.pt"` setting names the training run; copy the resulting trained weights to `Web/BackEnd/ML/LC.pt` for inference.

## Local Development

### Prerequisites

- Python 3.13 or later and `uv`
- Node.js 20 and npm, matching the frontend container's major version
- PostgreSQL, or Docker Compose to run the database
- Required model files listed above

The Python dependency file pins CUDA 12.4 builds of PyTorch and torchvision. Dependency installation depends on platform compatibility; CPU-only installations require adjusting those dependencies and their package source. The commands below reflect the repository configuration and have not been runtime-tested.

### 1. Clone the Repository

```bash
git clone https://github.com/SuphawitGot/CV-Webapplication.git
cd CV-Webapplication
```

### 2. Start PostgreSQL

To use the included database service:

```bash
docker compose up -d db
```

Create `Web/BackEnd/.env` with a connection string matching your database credentials:

```dotenv
DATABASE_URL=postgresql://postgres:YOUR_DATABASE_PASSWORD@localhost:5432/UserDB
```

Replace `YOUR_DATABASE_PASSWORD` with the configured database password. The Compose file currently contains development credentials; if changing them, keep the database service and backend connection string consistent.

### 3. Start the Backend

Run from `Web/BackEnd`:

```bash
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application creates its database tables during startup, so PostgreSQL must already be reachable.

### 4. Start the Frontend

Create `Web/frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

In a separate terminal, run from `Web/frontend`:

```bash
npm ci
npm run dev
```

### 5. Open the Application

| Page | URL |
| --- | --- |
| Detection dashboard | http://localhost:3000 |
| Sample user search page | http://localhost:3000/user |
| Interactive API documentation | http://localhost:8000/docs |
| Backend health message | http://localhost:8000/ |

Upload a video containing vehicles and a visible crosswalk. Detection starts automatically. Stop the current session before selecting another video through the dashboard.

## Docker Compose

The Compose configuration defines frontend, backend, and database services, with named volumes for PostgreSQL data, uploads, and captures.

Before building:

1. Add the missing model weights.
2. Set `dockerfile: dockerfile` under `services.frontend.build` in `docker-compose.yml`, or rename `Web/frontend/dockerfile` to `Dockerfile`. The committed filename is lowercase, while the Compose configuration does not specify it explicitly.
3. Review the backend PyTorch installation: the Dockerfile attempts a CPU installation, but `pyproject.toml` pins CUDA builds. These settings need to be made consistent for the target environment.

After resolving those prerequisites:

```bash
docker compose up --build
```

To stop the services:

```bash
docker compose down
```

The frontend uses port `3000`, the API uses `8000`, and PostgreSQL uses `5432`. For a remote deployment, set the frontend build argument `NEXT_PUBLIC_API_URL` to a browser-accessible backend URL, rebuild the frontend, and update the backend's allowed CORS origin. The current CORS configuration allows `http://localhost:3000` only.

## Detection API

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Backend status message |
| `POST` | `/upload` | Upload a video using multipart field `file` and start detection |
| `POST` | `/start` | Start processing a previously uploaded video |
| `POST` | `/pause` | Pause processing |
| `POST` | `/resume` | Resume processing |
| `POST` | `/stop` | Stop processing |
| `GET` | `/status` | Return `running` and `paused` flags |
| `GET` | `/stream` | Stream annotated frames as MJPEG |
| `GET` | `/violations` | Return captures from the current in-memory session |
| `GET` | `/captures/{filename}` | Serve images from the configured static capture directory |

The repository also contains `/auth/`, `/auth/all-users`, and `/auth/admin` routes. These are incomplete user-management scaffolding, not a working authenticated access-control system.

## Current Limitations

- **Missing model weights:** Crosswalk and plate detection require `best.pt` and `LC.pt`, which are not committed.
- **Capture directory mismatch:** The detector writes images to `Web/BackEnd/ML/captures`, while `/captures` serves `Web/BackEnd/captures`. Align these paths to make dashboard thumbnails accessible.
- **Session-only capture feed:** `/violations` reads an in-memory list that resets when detection starts. It does not retrieve historical records from PostgreSQL.
- **OCR startup timing:** Captures processed before EasyOCR finishes loading can remain at `Reading…` and skip the database write.
- **Shared processing state:** The backend uses one global video session and a global capture cooldown across vehicles. Independent concurrent sessions are not implemented.
- **Prototype user access:** The user page displays mock records. Detection endpoints are not protected by authentication, and the admin route does not implement a valid current-user check.
- **Detection semantics:** The trigger uses bounding-box overlap via a vehicle point, without stopping-duration checks or per-vehicle deduplication.

## Author

**Suphawit Sudsang**  
Computer Engineering, Rangsit University  
[GitHub](https://github.com/SuphawitGot) · [Repository](https://github.com/SuphawitGot/CV-Webapplication)

## License

No project license file is currently included in the repository.
