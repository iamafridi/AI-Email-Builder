import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import init_db, get_all_notifications, delete_notification, clear_all_notifications
from agent import EmailAgent, start_agent_thread

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


class PollResponse(BaseModel):
    status: str


@app.post("/api/poll")
def trigger_poll():
    agent.poll_now()
    return {"status": "polled"}
