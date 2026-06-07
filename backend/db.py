import sqlite3
import os
from datetime import datetime

DB_DIR = os.getenv("DB_DIR", os.path.join(os.path.dirname(__file__), "data"))
DB_PATH = os.path.join(DB_DIR, "emails.db")


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_emails (
            id TEXT PRIMARY KEY,
            processed_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            sender TEXT,
            subject TEXT,
            body_preview TEXT,
            priority TEXT,
            category TEXT,
            reason TEXT,
            received_at TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def is_processed(email_id: str) -> bool:
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM processed_emails WHERE id = ?", (email_id,)).fetchone()
    conn.close()
    return row is not None


def mark_processed(email_id: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO processed_emails (id, processed_at) VALUES (?, ?)",
        (email_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def save_notification(notification: dict):
    conn = get_connection()
    conn.execute(
        """INSERT OR IGNORE INTO notifications
           (id, sender, subject, body_preview, priority, category, reason, received_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            notification["id"],
            notification["sender"],
            notification["subject"],
            notification.get("body_preview", ""),
            notification["priority"],
            notification["category"],
            notification["reason"],
            notification["received_at"],
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_all_notifications():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM notifications ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_all_notifications():
    conn = get_connection()
    conn.execute("DELETE FROM notifications")
    conn.commit()
    conn.close()


def delete_notification(notification_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()
