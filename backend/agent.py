import time
import logging
import threading
import os

from db import is_processed, mark_processed, save_notification
from classifier import classify
from email_reader import get_reader

logger = logging.getLogger(__name__)


class EmailAgent:
    def __init__(self):
        self.reader = get_reader()
        self.poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
        self.last_polled = None
        self._stop = False
        self.paused = False

    def run(self):
        logger.info("Email agent started (poll interval: %ds)", self.poll_interval)
        while not self._stop:
            if self.paused:
                time.sleep(1)
                continue
            try:
                self._poll_once()
            except Exception as e:
                logger.error("Poll cycle failed: %s", e)
            time.sleep(self.poll_interval)

    def stop(self):
        self._stop = True

    def set_reader(self, mode=None, **kwargs):
        self.reader = get_reader(mode=mode, **kwargs)
        logger.info("Reader swapped to mode=%s", mode or os.getenv("EMAIL_MODE", "mock"))

    def set_paused(self, paused: bool):
        self.paused = paused
        logger.info("Agent %s", "paused" if paused else "resumed")

    def load_all_remaining(self):
        logger.info("Loading all remaining emails")
        emails = self.reader.get_all_remaining()
        if emails:
            logger.info("Loaded %d remaining emails", len(emails))
        for email in emails:
            email_id = email["id"]
            if is_processed(email_id):
                continue
            result = classify(email)
            if result.get("important", False):
                notification = {
                    "id": email_id,
                    "sender": email["sender"],
                    "subject": email["subject"],
                    "body_preview": email["body"][:200],
                    "priority": result.get("priority", "LOW"),
                    "category": result.get("category", "OTHER"),
                    "reason": result.get("reason", ""),
                    "received_at": email.get("received_at", ""),
                    "source": email.get("source", ""),
                }
                save_notification(notification)
                logger.info("Flagged as important: %s — %s", email_id, email["subject"])
            else:
                logger.info("Skipped (not important): %s — %s", email_id, email["subject"])
            mark_processed(email_id)
        self.last_polled = time.time()

    def poll_now(self):
        logger.info("Manual poll triggered")
        self._poll_once()

    def _poll_once(self):
        emails = self.reader.get_new_emails()
        if emails:
            logger.info("Polled %d new emails", len(emails))
        for email in emails:
            email_id = email["id"]
            if is_processed(email_id):
                logger.debug("Skipping (already processed): %s", email_id)
                continue

            result = classify(email)
            if result.get("important", False):
                notification = {
                    "id": email_id,
                    "sender": email["sender"],
                    "subject": email["subject"],
                    "body_preview": email["body"][:200],
                    "priority": result.get("priority", "LOW"),
                    "category": result.get("category", "OTHER"),
                    "reason": result.get("reason", ""),
                    "received_at": email.get("received_at", ""),
                    "source": email.get("source", ""),
                }
                save_notification(notification)
                logger.info("Flagged as important: %s — %s", email_id, email["subject"])
            else:
                logger.info("Skipped (not important): %s — %s", email_id, email["subject"])

            mark_processed(email_id)

        self.last_polled = time.time()


def start_agent_thread(agent):
    thread = threading.Thread(target=agent.run, daemon=True)
    thread.start()
    return thread
