import os
import shutil
import traceback
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import init_db, get_all_notifications, delete_notification, clear_all_notifications
from agent import EmailAgent, start_agent_thread

BACKEND_DIR = os.path.dirname(__file__)
CSV_FILE_PATH = os.path.join(BACKEND_DIR, "mock_emails.csv")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

agent = EmailAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initializing DB and agent")
    init_db()
    start_agent_thread(agent)
    yield
    logger.info("Shutting down")
    agent.stop()


app = FastAPI(title="AI Email Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    mode = os.getenv("EMAIL_MODE", "mock")
    return {"status": "ok", "mode": mode}


@app.get("/api/notifications")
def list_notifications():
    return get_all_notifications()


@app.get("/api/notifications/{notification_id}")
def get_notification(notification_id: str):
    notifications = get_all_notifications()
    for n in notifications:
        if n["id"] == notification_id:
            return n
    raise HTTPException(status_code=404, detail="Notification not found")


@app.delete("/api/notifications/{notification_id}")
def dismiss_notification(notification_id: str):
    delete_notification(notification_id)
    return {"status": "dismissed", "id": notification_id}


@app.delete("/api/notifications")
def clear_notifications():
    clear_all_notifications()
    return {"status": "cleared"}


@app.get("/api/stats")
def stats():
    notifications = get_all_notifications()
    total = len(notifications)
    high = sum(1 for n in notifications if n["priority"] == "HIGH")
    medium = sum(1 for n in notifications if n["priority"] == "MEDIUM")
    low = sum(1 for n in notifications if n["priority"] == "LOW")
    return {
        "total": total,
        "high": high,
        "medium": medium,
        "low": low,
        "last_polled": agent.last_polled,
    }


class ConfigBody(BaseModel):
    mode: str

class ConnectIMAPBody(BaseModel):
    host: str = "imap.gmail.com"
    port: int = 993
    user: str
    password: str


@app.get("/api/config")
def get_config():
    mode = os.getenv("EMAIL_MODE", "mock")
    imap_ok = bool(os.getenv("IMAP_USER") and os.getenv("IMAP_PASSWORD"))
    return {
        "mode": mode,
        "available_modes": ["mock", "csv", "imap"],
        "imap_connected": imap_ok,
        "csv_file": os.path.basename(CSV_FILE_PATH),
    }


@app.post("/api/config")
def set_config(body: ConfigBody):
    if body.mode not in ("mock", "csv", "imap"):
        raise HTTPException(status_code=400, detail=f"Invalid mode: {body.mode}")
    os.environ["EMAIL_MODE"] = body.mode
    agent.set_reader(mode=body.mode)
    return {"status": "ok", "mode": body.mode}


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    try:
        with open(CSV_FILE_PATH, "wb") as f:
            shutil.copyfileobj(file.file, f)
        os.environ["EMAIL_MODE"] = "csv"
        agent.set_reader(mode="csv", path=CSV_FILE_PATH)
        return {"status": "ok", "mode": "csv", "file": file.filename}
    except Exception as e:
        logger.error("CSV upload failed:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to load CSV: {e}")


@app.post("/api/connect-imap")
def connect_imap(body: ConnectIMAPBody):
    os.environ["IMAP_HOST"] = body.host
    os.environ["IMAP_PORT"] = str(body.port)
    os.environ["IMAP_USER"] = body.user
    os.environ["IMAP_PASSWORD"] = body.password
    agent.set_reader(mode="imap", host=body.host, port=body.port, user=body.user, password=body.password)
    return {"status": "ok", "mode": "imap", "host": body.host}


@app.post("/api/poll")
def trigger_poll():
    agent.poll_now()
    return {"status": "polled"}
